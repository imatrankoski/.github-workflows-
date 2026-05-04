import requests
import smtplib
import json
import os
import logging
import base64
from email.mime.text import MIMEText
from datetime import datetime
from zoneinfo import ZoneInfo
import time

URL = "https://data.nordpoolgroup.com/intraday/intraday-hourly-statistics?deliveryDate=latest&deliveryArea=FI"

# Environment variables
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "jereki/imatrankoskiFreedomTracker")
DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"

STATE_FILE_PATH = ".github/workflows/.last_alert.json"

# ============================================================
# LOGGING SETUP
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# ============================================================
# VALIDATION
# ============================================================
def validate_secrets():
    """Validate all required secrets are set"""
    logging.info("=" * 60)
    if DEBUG_MODE:
        logging.info("🔧 DEBUG MODE ENABLED - Sending test email every minute")
    else:
        logging.info("Starting Nord Pool price check")
    logging.info("=" * 60)
    
    missing = []
    if not EMAIL_FROM:
        missing.append("EMAIL_FROM")
    if not EMAIL_TO:
        missing.append("EMAIL_TO")
    if not EMAIL_PASS:
        missing.append("EMAIL_PASS")
    
    if missing:
        error_msg = f"Missing GitHub secrets: {', '.join(missing)}"
        logging.error(f"❌ {error_msg}")
        logging.error("Please add these secrets in GitHub Settings → Secrets and variables → Actions")
        raise ValueError(error_msg)
    
    logging.info("✓ All secrets validated")

# ============================================================
# DATA FETCHING
# ============================================================
def fetch_data(retries=3):
    """Fetch latest Nord Pool data with retry logic"""
    for attempt in range(retries):
        try:
            r = requests.get(URL, timeout=10)
            r.raise_for_status()
            logging.info("✓ Data fetched successfully")
            return r.json()
        except Exception as e:
            logging.warning(f"Fetch failed (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2)
    
    error_msg = "Failed to fetch data after retries"
    logging.error(f"❌ {error_msg}")
    raise Exception(error_msg)

# ============================================================
# DATA PROCESSING
# ============================================================
def format_time_finnish(start, end):
    """Convert ISO timestamps to Finnish local time"""
    try:
        dt_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
        dt_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
        
        fi_tz = ZoneInfo("Europe/Helsinki")
        dt_start = dt_start.astimezone(fi_tz)
        dt_end = dt_end.astimezone(fi_tz)
        
        return dt_start.strftime("%d.%m.%Y %H:%M") + "–" + dt_end.strftime("%H:%M")
    except Exception as e:
        logging.warning(f"Time conversion failed: {e}")
        return f"{start} → {end}"


def extract_negative_rows(data):
    """Extract negative price entries from API response"""
    results = []
    
    try:
        for row in data.get("multiAreaEntries", []):
            for entry in row.get("entryPerArea", {}).values():
                try:
                    price = float(entry.get("value"))
                except (ValueError, TypeError):
                    continue
                
                if price < 0:
                    results.append({
                        "start": entry.get("deliveryStart"),
                        "end": entry.get("deliveryEnd"),
                        "price": price,
                        "vwap1h": entry.get("vwap1h"),
                        "vwap3h": entry.get("vwap3h"),
                    })
        
        results = sorted(results, key=lambda x: x["start"])
        logging.info(f"✓ Data processed: {len(results)} negative price(s) found")
        return results
    
    except Exception as e:
        logging.error(f"❌ Error processing data: {e}")
        raise

# ============================================================
# STATE MANAGEMENT (GitHub API)
# ============================================================
def get_state_from_github():
    """Fetch current state file from GitHub"""
    try:
        if not GITHUB_TOKEN:
            logging.warning("⚠ GITHUB_TOKEN not available, skipping duplicate check")
            return None
        
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents/{STATE_FILE_PATH}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            return json.loads(content), data.get("sha")
        elif response.status_code == 404:
            return None, None
        else:
            logging.warning(f"⚠ GitHub API error: {response.status_code}")
            return None, None
    
    except Exception as e:
        logging.warning(f"⚠ Could not fetch state from GitHub: {e}")
        return None, None


def save_state_to_github(rows):
    """Save state file to GitHub"""
    try:
        if not GITHUB_TOKEN:
            logging.warning("⚠ GITHUB_TOKEN not available, skipping state save")
            return
        
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        state_data = {
            "rows": rows,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        content = base64.b64encode(json.dumps(state_data, indent=2).encode()).decode()
        
        # Get current SHA if file exists
        url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents/{STATE_FILE_PATH}"
        get_response = requests.get(url, headers=headers, timeout=10)
        
        sha = None
        if get_response.status_code == 200:
            sha = get_response.json().get("sha")
        
        # Create or update file
        payload = {
            "message": f"Update alert state - {len(rows)} negative price(s) detected",
            "content": content
        }
        
        if sha:
            payload["sha"] = sha
        
        response = requests.put(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            logging.info("✓ State saved to GitHub")
        else:
            logging.warning(f"⚠ Could not save state: {response.status_code}")
    
    except Exception as e:
        logging.warning(f"⚠ Error saving state to GitHub: {e}")


def already_alerted(rows):
    """Check if we already sent alert for these prices"""
    try:
        state, _ = get_state_from_github()
        if state and state.get("rows") == rows:
            logging.info("ℹ Already alerted for these values (duplicate check)")
            return True
        return False
    except Exception as e:
        logging.warning(f"⚠ Duplicate check failed: {e}")
        return False

# ============================================================
# EMAIL FORMATTING & SENDING
# ============================================================
def format_email(rows, is_debug=False):
    """Generate HTML email with price table"""
    debug_badge = "<span style='background-color: #ff9800; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;'>DEBUG MODE</span>" if is_debug else ""
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
    <h3>⚡ Negative electricity prices detected (FI) {debug_badge}</h3>
    
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; max-width: 600px;">
        <tr style="background-color: #f2f2f2; font-weight: bold;">
            <th style="padding: 10px;">Delivery Time</th>
            <th style="padding: 10px;">Price (€/MWh)</th>
            <th style="padding: 10px;">VWAP 1H</th>
            <th style="padding: 10px;">VWAP 3H</th>
        </tr>
    """
    
    for r in rows:
        delivery = format_time_finnish(r["start"], r["end"])
        price_color = "red" if r["price"] < 0 else "green"
        
        html += f"""
        <tr>
            <td style="padding: 8px;">{delivery}</td>
            <td style="padding: 8px; color: {price_color}; font-weight: bold;">{r['price']:.2f}</td>
            <td style="padding: 8px;">{r['vwap1h'] if r['vwap1h'] else '-'}</td>
            <td style="padding: 8px;">{r['vwap3h'] if r['vwap3h'] else '-'}</td>
        </tr>
        """
    
    html += """
    </table>
    
    <p style="font-size: 12px; color: #666; margin-top: 20px;">
    <strong>Notes:</strong><br>
    • Delivery times are shown in Finnish local time (Europe/Helsinki)<br>
    • VWAP1H = Volume Weighted Average Price over 1 hour<br>
    • VWAP3H = Volume Weighted Average Price over 3 hours<br>
    • Data source: Nord Pool Intraday Market
    </p>
    
    </body>
    </html>
    """
    
    return html


def send_email(body, subject=None):
    """Send HTML email via Gmail SMTP"""
    try:
        msg = MIMEText(body, "html")
        msg["Subject"] = subject or "⚡ Nord Pool Alert: Negative Prices (FI)"
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASS)
            server.send_message(msg)
        
        logging.info(f"✓ Email sent to {EMAIL_TO}")
    
    except smtplib.SMTPAuthenticationError:
        logging.error("❌ Email authentication failed - check EMAIL_FROM and EMAIL_PASS")
        raise
    except Exception as e:
        logging.error(f"❌ Failed to send email: {e}")
        raise

# ============================================================
# MAIN
# ============================================================
def main():
    try:
        validate_secrets()
        
        if DEBUG_MODE:
            # Debug mode: Always send test email with current time
            logging.info("🔧 Running in DEBUG mode - sending test email")
            test_rows = [{
                "start": datetime.now(ZoneInfo("UTC")).isoformat(),
                "end": datetime.now(ZoneInfo("UTC")).isoformat(),
                "price": -15.50,
                "vwap1h": -12.75,
                "vwap3h": -10.25
            }]
            body = format_email(test_rows, is_debug=True)
            subject = f"🧪 [TEST] Debug Mode Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            send_email(body, subject)
            logging.info("=" * 60)
            logging.info("✓ Debug email sent successfully")
            logging.info("=" * 60)
        else:
            # Normal mode: Check for actual negative prices
            data = fetch_data()
            negatives = extract_negative_rows(data)
            
            if negatives:
                logging.info(f"Found {len(negatives)} negative price(s)")
                
                if not already_alerted(negatives):
                    body = format_email(negatives)
                    send_email(body)
                    save_state_to_github(negatives)
                    logging.info("=" * 60)
                    logging.info("✓ Alert sent and state saved")
                    logging.info("=" * 60)
                else:
                    logging.info("=" * 60)
                    logging.info("No new alerts needed (already notified)")
                    logging.info("=" * 60)
            else:
                logging.info("=" * 60)
                logging.info("✓ No negative prices detected")
                logging.info("=" * 60)
    
    except Exception as e:
        logging.error("=" * 60)
        logging.error(f"❌ Fatal error: {e}")
        logging.error("=" * 60)
        exit(1)


if __name__ == "__main__":
    main()
name=README.md
# ⚡ Nord Pool Negative Price Alert (FI)

Automated monitoring system that detects negative electricity prices in the Finland Nord Pool market and sends email alerts.

## 🎯 Features

- ✅ Monitors Nord Pool intraday prices for **Finland only**
- ✅ Sends **HTML email alerts** with formatted price tables
- ✅ Automatic **timezone conversion** to Finnish local time (Europe/Helsinki)
- ✅ Includes **VWAP 1H and 3H** metrics
- ✅ **Duplicate alert prevention** (persisted via GitHub API)
- ✅ Automatic retry logic with error handling
- ✅ Comprehensive logging to file and console
- ✅ Runs every **10 minutes** via GitHub Actions (production)
- ✅ **Debug mode** - sends test email every **1 minute** for testing
- ✅ Secret validation with clear error messages
- ✅ Email authentication validation

## 📋 Prerequisites

1. **GitHub Account** with this repository
2. **Gmail Account** with [App Password](https://support.google.com/accounts/answer/185833) enabled
3. **GitHub Secrets** configured in repository settings

## 🔧 Setup Instructions

### Step 1: Generate Gmail App Password

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Navigate to **Security** → **App passwords**
3. Select:
   - **App**: Mail
   - **Device**: Windows Computer (or your device)
4. Copy the **16-character password**
5. ⚠️ **Note**: Gmail only shows this password once!

### Step 2: Configure GitHub Secrets

1. Go to your repository settings
2. Click **Secrets and variables** → **Actions**
3. Create these secrets:
   - `EMAIL_FROM`: Your Gmail address (e.g., `yourname@gmail.com`)
   - `EMAIL_TO`: Recipient email address
   - `EMAIL_PASS`: The 16-character Gmail App Password (without spaces)

> **Note**: `GITHUB_TOKEN` is automatically provided by GitHub Actions

### Step 3: Enable Workflows

1. Go to the **Actions** tab in your repository
2. Enable "Nordpool Price Check" workflow (production - every 10 minutes)
3. Optionally enable "Debug Mode" workflow (testing - every 1 minute)

## 🚀 Usage

### Production Mode (Default)

The `Nordpool Price Check` workflow runs automatically **every 10 minutes** and:
- Fetches latest Nord Pool prices for Finland
- Detects **negative prices only**
- Sends email alerts only when negative prices are found
- Prevents duplicate alerts for the same prices
- Logs all activity to `app.log` artifact

### Debug Mode (Testing)

The `Debug Mode` workflow runs **every 1 minute** and:
- Sends a test email with mock negative price data
- Useful for validating email setup works correctly
- Labeled with `[TEST]` and current timestamp in subject line
- **Disable this workflow when done testing** to avoid email spam

#### How to Toggle Debug Mode

**Enable Debug Mode:**
- In repository **Actions** tab → **Debug Mode - Test Email Every Minute** → **Enable workflow**

**Disable Debug Mode:**
- In repository **Actions** tab → **Debug Mode - Test Email Every Minute** → **Disable workflow** (three dots menu)
- Or delete `.github/workflows/debug-schedule.yml` file

**Manual Test Trigger:**
- Go to **Actions** tab → **Debug Mode - Test Email Every Minute**
- Click **Run workflow** → **Run workflow**

## 📧 Email Alert Example

You'll receive an HTML formatted email with:
- **Delivery Time** (Finnish local time)
- **Negative Price** (€/MWh)
- **VWAP 1H** and **VWAP 3H** metrics
- Source attribution to Nord Pool Intraday Market

## 🔍 Monitoring & Debugging

### View Workflow Runs

1. Go to **Actions** tab
2. Select a workflow ("Nordpool Price Check" or "Debug Mode")
3. Click on a run to see detailed logs
4. Download `app-logs` or `debug-logs` artifact if the run failed

### Common Issues

**Email not sending?**
- Verify `EMAIL_FROM` and `EMAIL_PASS` are correct
- Check that Gmail Account has 2FA enabled and App Password is generated
- Review logs in workflow artifacts

**No prices detected?**
- Nord Pool API only shows prices when they exist
- Check the [Nord Pool website](https://www.nordpoolgroup.com/) to verify prices are available

**Duplicate alerts?**
- The script uses GitHub API to track previously alerted prices
- Ensure `GITHUB_TOKEN` secret is properly configured (usually automatic)

## 🛠️ Configuration

### Modify Check Frequency

Edit `.github/workflows/price-check.yml` line 6:
```yaml
on:
  schedule:
    - cron: "*/10 * * * *"  # Change 10 to desired minutes
```

Cron format: `"minute hour day-of-month month day-of-week"`
- `"*/5 * * * *"` = Every 5 minutes
- `"0 */2 * * *"` = Every 2 hours
- `"0 9 * * *"` = Daily at 9:00 AM

### Modify Debug Frequency

Edit `.github/workflows/debug-schedule.yml` line 5:
```yaml
on:
  schedule:
    - cron: "* * * * *"  # Every 1 minute (default)
```

## 📝 Logs

Logs are saved to `app.log` and contain:
- Timestamp of each operation
- Data fetch status
- Price analysis results
- Email sending confirmation
- Any errors or warnings

Download logs from workflow artifacts:
1. **Actions** tab → Failed run → **Artifacts** → `app-logs` or `debug-logs`

## 📞 Support

For issues:
1. Check the logs in workflow artifacts
2. Verify all GitHub secrets are set correctly
3. Test manually with **Debug Mode** workflow
4. Review GitHub Actions documentation

## 📄 License

Free to use and modify for personal use.
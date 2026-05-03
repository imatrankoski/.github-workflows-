[README.md](https://github.com/user-attachments/files/27322942/README.md)
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
- ✅ Runs every **10 minutes** via GitHub Actions
- ✅ Secret validation with clear error messages

## 📋 Prerequisites

1. **GitHub Account** with a repository
2. **Gmail Account** with [App Password](https://support.google.com/accounts/answer/185833) enabled
3. **GitHub Secrets** configured (see Setup section)

## 🔧 Setup Instructions

### Step 1: Generate Gmail App Password

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Navigate to **Security** → **App passwords**
3. Select:
   - **App**: Mail
   - **Device**: Windows Computer (or your device)
4. Copy the **16-character password**
5. ⚠️ **Note**: Gmail only shows this password once!

### Step 2: Create GitHub Repository

1. Create a new repository named `nordpool-alert` (or your preferred name)
2. Clone it locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/nordpool-alert.git
   cd nordpool-alert

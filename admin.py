#!/usr/bin/env python3
"""
Google Sheets Setup Verification Script
Run this to check if everything is configured correctly
"""

import sys
import os

print("=" * 70)
print("🔧 GOOGLE SHEETS SETUP VERIFICATION")
print("=" * 70)

# Check 1: Package Installation
print("\n📦 Step 1: Checking required packages...")
try:
    import gspread
    print("   ✅ gspread installed")
except ImportError:
    print("   ❌ gspread NOT installed")
    print("   💡 Fix: pip install gspread")
    sys.exit(1)

try:
    from google.oauth2.service_account import Credentials
    print("   ✅ google-auth installed")
except ImportError:
    print("   ❌ google-auth NOT installed")
    print("   💡 Fix: pip install google-auth")
    sys.exit(1)

# Check 2: Credentials from Environment Variables
print("\n🔑 Step 2: Checking credentials...")

creds_dict = {
    "type": "service_account",
    "project_id": os.environ.get("GOOGLE_PROJECT_ID", ""),
    "private_key_id": os.environ.get("GOOGLE_PRIVATE_KEY_ID", ""),
    "private_key": os.environ.get("GOOGLE_PRIVATE_KEY", "").replace("\\n", "\n"),
    "client_email": os.environ.get("GOOGLE_CLIENT_EMAIL", ""),
    "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.environ.get("GOOGLE_CLIENT_X509_CERT_URL", "")
}

missing = [k for k, v in creds_dict.items() if not v and k not in ["auth_uri", "token_uri", "auth_provider_x509_cert_url"]]
if missing:
    print(f"   ❌ Missing environment variables: {missing}")
    print("   💡 Set these in Render → Environment Variables")
    sys.exit(1)

print("   ✅ Credentials loaded from environment variables")
SERVICE_EMAIL = creds_dict["client_email"]
print(f"   📧 Service Account: {SERVICE_EMAIL}")

# Check 3: Sheet ID
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "1yDTFJ6g0HhC7vA1PT1cfab1VwET467eu0xPW7TGmUQ4")
print(f"\n📋 Step 3: Checking Sheet ID...")
print(f"   Sheet ID: {SHEET_ID}")
print(f"   Sheet URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")

# Check 4: Connection Test
print(f"\n🔌 Step 4: Testing connection...")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    from datetime import datetime

    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    print("   ✅ Credentials created")

    client = gspread.authorize(creds)
    print("   ✅ Client authorized")

    sheet = client.open_by_key(SHEET_ID)
    print(f"   ✅ Spreadsheet opened: '{sheet.title}'")

    worksheet = sheet.sheet1
    print(f"   ✅ Worksheet accessed: '{worksheet.title}'")

    all_values = worksheet.get_all_values()
    print(f"   📊 Current rows: {len(all_values)}")

    if all_values:
        headers = all_values[0]
        print(f"   📝 Headers: {headers}")
        expected_headers = ["hall_ticket", "page", "timestamp"]
        if headers != expected_headers:
            print(f"   ⚠️  WARNING: Headers don't match!")
            print(f"      Expected: {expected_headers}")
            print(f"      Found: {headers}")
    else:
        print("   ⚠️  Sheet is empty! Add headers: hall_ticket | page | timestamp")

    print("\n✍️  Step 5: Writing test data...")
    test_row = [
        f"TEST_{datetime.now().strftime('%H%M%S')}",
        "TestPage",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]
    worksheet.append_row(test_row)
    print(f"   ✅ Test data written: {test_row}")

    all_values_after = worksheet.get_all_values()
    print(f"   ✅ Verified! Rows after write: {len(all_values_after)}")

    print("\n" + "=" * 70)
    print("🎉 SUCCESS! Everything is working perfectly!")
    print("=" * 70)

except gspread.exceptions.APIError as e:
    print(f"\n❌ API Error: {e}")
    print(f"\n💡 Share the sheet with: {SERVICE_EMAIL}")

except gspread.exceptions.SpreadsheetNotFound:
    print(f"\n❌ Spreadsheet Not Found! Check Sheet ID: {SHEET_ID}")

except Exception as e:
    print(f"\n❌ Unexpected Error: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 70)

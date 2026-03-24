#!/usr/bin/env python3
"""
youtube_auth_setup.py
─────────────────────
Run this ONCE on your PC/phone to get YouTube OAuth credentials.
Then copy the printed JSON into your GitHub Secret: YOUTUBE_CREDENTIALS

Steps:
  1. Go to https://console.cloud.google.com
  2. Create project → Enable "YouTube Data API v3"
  3. Create OAuth 2.0 credentials (Desktop app type)
  4. Download client_secret_xxxx.json
  5. Run: python youtube_auth_setup.py client_secret_xxxx.json
  6. Browser opens → Login → Allow
  7. Copy the printed JSON → paste into GitHub Secret
"""

import sys, json

def main():
    if len(sys.argv) < 2:
        print("Usage: python youtube_auth_setup.py client_secret_YOUR_FILE.json")
        sys.exit(1)

    client_secret_file = sys.argv[1]

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Install first: pip install google-auth-oauthlib google-api-python-client")
        sys.exit(1)

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
    creds = flow.run_local_server(port=8080, open_browser=True)

    creds_dict = {
        "token":         creds.token,
        "refresh_token": creds.refresh_token,
        "client_id":     creds.client_id,
        "client_secret": creds.client_secret,
        "token_uri":     creds.token_uri,
    }

    creds_json = json.dumps(creds_dict)

    print("\n" + "="*60)
    print("✅ SUCCESS! Copy this JSON into GitHub Secret:")
    print("   Secret name: YOUTUBE_CREDENTIALS")
    print("="*60)
    print(creds_json)
    print("="*60)

    # Also save to file as backup
    with open("youtube_credentials.json", "w") as f:
        json.dump(creds_dict, f, indent=2)
    print("\n💾 Also saved to: youtube_credentials.json")
    print("⚠️  Keep this file private! Never upload it to GitHub.")

if __name__ == "__main__":
    main()

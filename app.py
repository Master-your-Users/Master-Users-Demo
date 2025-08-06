import os
import json
from flask import Flask, redirect, request, session, url_for, render_template
from dotenv import load_dotenv
import requests

# טען משתני סביבה מהקובץ .env
load_dotenv()

# Debug: Print environment variables
print("Debug - Environment Variables:")
print(f"CLIENT_ID: {os.getenv('CLIENT_ID')}")
print(f"CLIENT_SECRET: {os.getenv('CLIENT_SECRET')}")
print(f"FLASK_SECRET_KEY: {os.getenv('FLASK_SECRET_KEY')}")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# נתונים רגישים ל־OAuth
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8080/oauth2callback")
SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"

# 🟢 דף הבית
@app.route('/')
def index():
    return render_template('index.html')

# 🟢 התחלת תהליך ההתחברות עם המייל
@app.route('/authorize')
def authorize():
    user_email = request.args.get("email")
    if not user_email:
        return "Missing email", 400

    session["user_email"] = user_email

    state = os.urandom(16).hex()
    session["state"] = state

    auth_uri = (
        f"{AUTH_URL}"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPE}"
        f"&state={state}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return redirect(auth_uri)

# 🟢 נקודת חזרה אחרי התחברות לגוגל
@app.route('/oauth2callback')
def oauth2callback():
    if request.args.get("state") != session.get("state"):
        return "Invalid state parameter", 400

    code = request.args.get("code")

    # שלח את הקוד ל־Google כדי לקבל access token
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    token_response = requests.post(TOKEN_URL, data=data)
    if token_response.status_code != 200:
        error_details = token_response.json() if token_response.content else "No error details available"
        print(f"Token request failed with status {token_response.status_code}. Error details: {error_details}")
        return f"Failed to retrieve access token. Status: {token_response.status_code}, Details: {error_details}", 500

    token_json = token_response.json()
    
    # Create token data dictionary for gmail_utils
    token_data = {
        'access_token': token_json.get('access_token'),
        'refresh_token': token_json.get('refresh_token')
    }

    # Use the gmail_utils function to scan for accounts
    from gmail_utils import scan_gmail_for_accounts
    found_accounts = scan_gmail_for_accounts(token_data)

    if not found_accounts:
        message = "No registered accounts found for this email address."
    else:
        message = f"Found {len(found_accounts)} registered accounts across various services."

    return render_template("results.html", accounts=found_accounts, found_count=len(found_accounts), message=message)

# 🟢 דף תנאי שימוש
@app.route('/terms')
def terms():
    return render_template("terms.html")

# 🟢 דף מדיניות פרטיות
@app.route('/privacy')
def privacy():
    return render_template("privacy.html")

# 🟢 דף אודות (בעתיד)
@app.route('/about')
def about():
    return render_template("about.html")

# 🟢 הפעלת השרת
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
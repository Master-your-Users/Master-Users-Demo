import base64
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

# מיפוי שירותים לפי שולחים, נושאים ותוכן
SERVICE_PATTERNS = {
    "Facebook": {
        "sender": ["@facebookmail.com"],
        "subject": ["Welcome to Facebook"],
        "body": ["Your account has been created"]
    },
    "Dropbox": {
        "sender": ["@dropbox.com"],
        "subject": ["we noticed a new sign"],
        "body": ["just signed in to your Dropbox"]
    },
    "PayPal": {
        "sender": ["service@paypal.co.il"],
        "subject": ["Welcome to PayPal.Me"],
        "body": ["Welcome to PayPal.Me"]
    },
    "Netflix": {
        "sender": ["@netflix.com"],
        "subject": ["כמעט סיימנו"],
        "body": ["זה הזמן ליצור את החשבון שלך"]
    },
    "Heroku": {
        "sender": ["@heroku.com"],
        "subject": ["Confirm your account"],
        "body": ["Thanks for signing up with Heroku"]
    },
    "Vimeo": {
        "sender": ["@vimeo.com"],
        "subject": ["You're in!"],
        "body": ["The world of video is your oyster"]
    },
    "Asana": {
        "sender": ["@asana.com"],
        "subject": ["You started your first project"],
        "body": ["Cross-functional project plan"]
    },
    "Stripe": {
        "sender": ["@stripe.com"],
        "subject": ["Start setting up your Stripe account"],
        "body": ["Welcome – let’s get started"]
    },
    "Slack": {
        "sender": ["@slack.com"],
        "subject": ["free trial of Slack Pro"],
        "body": ["30-day trial of Slack Pro"]
    },
    "Shopify": {
        "sender": ["@shopify.com"],
        "subject": ["Let’s set up your new store"],
        "body": ["we make it easier"]
    },
    "Gumroad": {
        "sender": ["@gumroad.com"],
        "subject": ["Your authentication token"],
        "body": ["We have detected a new login"]
    },
}

def scan_gmail_for_accounts(token_data):
    creds = Credentials(
        token=token_data['access_token'],
        refresh_token=token_data['refresh_token'],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET")
    )

    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', maxResults=4000).execute()
    messages = results.get('messages', [])

    found_accounts = []

    for msg in messages:
        msg_detail = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        payload = msg_detail.get('payload', {})
        headers = payload.get('headers', [])

        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')

        data = ''
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/html':
                    data = part['body'].get('data', '')
                    break
        else:
            data = payload.get('body', {}).get('data', '')

        body = ''
        if data:
            decoded_bytes = base64.urlsafe_b64decode(data)
            soup = BeautifulSoup(decoded_bytes, "html.parser")
            body = soup.get_text()

        for service_name, patterns in SERVICE_PATTERNS.items():
            sender_match = any(s in sender for s in patterns['sender'])
            subject_match = any(s in subject for s in patterns['subject'])
            body_match = any(s in body for s in patterns['body'])

            if sender_match or subject_match or body_match:
                domain = patterns['sender'][0].split('@')[-1] if '@' in patterns['sender'][0] else patterns['sender'][0]
                account = {
                    'service': service_name,
                    'domain': domain
                }
                if account not in found_accounts:
                    found_accounts.append(account)

    return found_accounts
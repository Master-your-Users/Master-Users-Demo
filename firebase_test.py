import firebase_admin
from firebase_admin import credentials

# טען את הקובץ עם ההרשאות
cred = credentials.Certificate("serviceAccountKey.json")

# אתחול החיבור לפיירבייס
firebase_admin.initialize_app(cred)

print("✅ התחברת בהצלחה ל-Firebase!")
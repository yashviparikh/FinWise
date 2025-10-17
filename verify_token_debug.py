# verify_token_debug.py
import firebase_admin, json, os
from firebase_admin import credentials, auth
import sys

sa_path = os.path.join(os.getcwd(), "finwise-cfa37-firebase-adminsdk-fbsvc-dbb2e2057f.json")
if not os.path.exists(sa_path):
    print("serviceAccountKey.json NOT found at", sa_path)
    sys.exit(1)

cred = credentials.Certificate(sa_path)
try:
    firebase_admin.initialize_app(cred)
except Exception:
    # already initialized ok
    pass

token = input("Paste the FULL idToken here (it will not be shared):\n")
try:
    decoded = auth.verify_id_token(token.strip())
    print("VERIFY OK. decoded keys:", list(decoded.keys()))
    print("uid:", decoded.get("uid"))
    print("email:", decoded.get("email"))
except Exception as e:
    print("VERIFY ERROR:", type(e).__name__, str(e))

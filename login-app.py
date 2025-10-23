from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from pymongo import MongoClient
import bcrypt
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
import os
import json
import random
import datetime

app = Flask(__name__)

# ---------------------- CORS CONFIG ----------------------
FRONTEND_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]
CORS(app, resources={r"/*": {"origins": FRONTEND_ORIGINS}}, supports_credentials=True)

@app.before_request
def handle_preflight():
    """Ensure every OPTIONS preflight gets HTTP 200 OK"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response


# ---------------------- MONGODB SETUP ----------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["th3ee"]
users = db["users"]

# ---------------------- FIREBASE (optional) ----------------------
sa_path = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")
if os.path.exists(sa_path):
    try:
        cred = credentials.Certificate(sa_path)
        firebase_admin.initialize_app(cred)
        with open(sa_path, "r") as f:
            sa = json.load(f)
        print("✅ Firebase Admin initialized for project:", sa.get("project_id"))
    except Exception as e:
        print("⚠️ Firebase Admin init error:", e)
else:
    print("ℹ️ serviceAccountKey.json not found (ok for dev OTP flow).")

# ---------------------- HELPERS ----------------------
def gen_otp(n=6):
    return ''.join(str(random.randint(0, 9)) for _ in range(n))

def normalize_phone(phone):
    if not phone:
        return None
    s = str(phone).strip()
    if s.startswith('+'):
        return s
    digits = ''.join(ch for ch in s if ch.isdigit())
    if len(digits) == 10:
        return '+91' + digits
    return '+' + digits

def get_user_query(data):
    return {"phone": data.get("phone")} if data.get("phone") else {"email": data.get("email")}

# ---------------------- SIGNUP ----------------------
@app.route('/signup', methods=['OPTIONS', 'POST'])
def signup():
    if request.method == 'OPTIONS':
        return ('', 200)
    data = request.json or {}
    name = data.get('name')
    phone = data.get('phone')
    password = data.get('password')

    if not phone or not password:
        return jsonify({"status": "fail", "message": "phone and password required"}), 400

    phone_norm = normalize_phone(phone)
    if users.find_one({"phone": phone_norm}):
        return jsonify({"status": "fail", "message": "User already exists"}), 409

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users.insert_one({"name": name, "phone": phone_norm, "password": hashed, "cart": []})
    return jsonify({"status": "success", "message": "Signup successful"}), 200


# ---------------------- LOGIN ----------------------
@app.route('/login', methods=['OPTIONS', 'POST'])
def login():
    if request.method == 'OPTIONS':
        return ('', 200)
    try:
        data = request.json or {}
        phone = str(data.get('phone') or '')
        password = data.get('password') or ''
        phone_norm = normalize_phone(phone)

        user = users.find_one({"phone": phone_norm}) or users.find_one({"phone": phone})
        if not user:
            return jsonify({"status": "fail", "message": "Invalid credentials"}), 401

        stored = user.get('password')
        stored_bytes = stored if isinstance(stored, (bytes, bytearray)) else bytes(stored)

        if bcrypt.checkpw(password.encode('utf-8'), stored_bytes):
            return jsonify({
                "status": "success",
                "message": "Login successful",
                "user": {
                    "name": user.get("name", ""),
                    "phone": user.get("phone"),
                    "cart": user.get("cart", [])
                }
            }), 200
        else:
            return jsonify({"status": "fail", "message": "Invalid credentials"}), 401

    except Exception as e:
        import traceback
        print("Exception in /login:", type(e).__name__, e)
        traceback.print_exc()
        return jsonify({"status": "fail", "message": "Server error"}), 500



@app.route('/google-login', methods=['OPTIONS', 'POST'])
def google_login():
    if request.method == 'OPTIONS':
        return ('', 200)
    data = request.json or {}
    id_token = data.get('idToken') or data.get('id_token') or data.get('token')
    if not id_token:
        return jsonify({"status":"fail","message":"No idToken provided"}), 400

    try:
        decoded = firebase_auth.verify_id_token(id_token)
        uid = decoded.get('uid')
        email = decoded.get('email')
        name = decoded.get('name') or (email.split('@')[0] if email else 'User')

        user = users.find_one({"firebase_uid": uid}) or users.find_one({"email": email})
        if not user:
            new_user = {"name": name, "email": email, "firebase_uid": uid, "cart": []}
            users.insert_one(new_user)
            user = users.find_one({"firebase_uid": uid})

        user_out = {"name": user.get("name"), "email": user.get("email"), "cart": user.get("cart", [])}
        return jsonify({"status":"success","message":"Google login OK","user":user_out}), 200

    except Exception as e:
        print("Google login error:", e)
        return jsonify({"status":"fail","message":"Invalid token","error": str(e)}), 401

# ---------------------- OTP RESET ----------------------
@app.route('/send-otp', methods=['OPTIONS', 'POST'])
def send_otp():
    if request.method == 'OPTIONS':
        return ('', 200)

    data = request.json or {}
    phone_raw = data.get('phone')
    phone = normalize_phone(phone_raw)
    if not phone:
        return jsonify({"status": "fail", "message": "Phone number required"}), 400

    otp = gen_otp(6)
    otp_ts = datetime.datetime.utcnow()

    users.update_one(
        {"phone": phone},
        {"$set": {"otp": otp, "otp_ts": otp_ts}},
        upsert=True
    )

    # In real life, send SMS here. For now, print to console.
    print(f"[DEV OTP] Phone={phone} OTP={otp}")
    return jsonify({"status": "success", "message": "OTP sent successfully"}), 200


@app.route('/verify-otp', methods=['OPTIONS', 'POST'])
def verify_otp():
    if request.method == 'OPTIONS':
        return ('', 200)

    data = request.json or {}
    phone = normalize_phone(data.get('phone'))
    otp = str(data.get('otp', '')).strip()

    user = users.find_one({"phone": phone})
    if not user:
        return jsonify({"status": "fail", "message": "User not found"}), 404

    if user.get('otp') != otp:
        return jsonify({"status": "fail", "message": "Invalid OTP"}), 400

    if (datetime.datetime.utcnow() - user['otp_ts']).seconds > 600:
        return jsonify({"status": "fail", "message": "OTP expired"}), 400

    return jsonify({"status": "success", "message": "OTP verified successfully"}), 200


@app.route('/reset-password', methods=['OPTIONS', 'POST'])
def reset_password():
    if request.method == 'OPTIONS':
        return ('', 200)

    data = request.json or {}
    phone = normalize_phone(data.get('phone'))
    new_password = data.get('newPassword')

    if not phone or not new_password:
        return jsonify({"status": "fail", "message": "Missing data"}), 400

    hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    users.update_one(
        {"phone": phone},
        {"$set": {"password": hashed_pw, "otp": None, "otp_ts": None}}
    )

    return jsonify({"status": "success", "message": "Password reset successfully"}), 200

# ---------------------- MAIN ----------------------
if __name__ == '__main__':
    # Run on port 5001 to avoid clash with FinWise backend
    app.run(debug=True, port=5001)

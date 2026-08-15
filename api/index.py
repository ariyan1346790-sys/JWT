import os
import sys
import json
import urllib3
import requests
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Pb2'))
try:
    import MajoRLoGinrEq_pb2
    import MajoRLoGinrEs_pb2
except ImportError:
    pass

STATIC_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
STATIC_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
CLIENT_VERSION = "1.126.4"

# Global Reusable Session for High-Speed Connection Pooling
SESSION = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=1)
SESSION.mount('https://', adapter)

def encrypt_proto(payload_bytes: bytes) -> bytes:
    cipher = AES.new(STATIC_KEY, AES.MODE_CBC, STATIC_IV)
    return cipher.encrypt(pad(payload_bytes, AES.block_size))

def get_official_garena_token(uid, password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    headers = {
        "Host": "100067.connect.garena.com",
        "User-Agent": "GarenaMSDK/5.5.2P3(SM-A515F;Android 12;en-US;IND;)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "keep-alive"
    }
    data = {
        "uid": str(uid).strip(),
        "password": str(password).strip(),
        "response_type": "token",
        "client_type": "2",
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067"
    }
    try:
        resp = SESSION.post(url, headers=headers, data=data, verify=False, timeout=6)
        if resp.status_code == 200:
            js = resp.json()
            return js.get("open_id"), js.get("access_token")
        return None, None
    except Exception:
        return None, None

def build_major_login_payload(open_id: str, access_token: str) -> bytes:
    msg = MajoRLoGinrEq_pb2.MajorLogin()
    msg.event_time = str(datetime.now())[:-7]
    msg.game_name = "free fire"
    msg.platform_id = 2
    msg.client_version = CLIENT_VERSION
    msg.client_version_code = "2024010012"
    msg.system_software = "Android OS 11"
    msg.system_hardware = "Handheld"
    msg.device_type = "Handheld"
    msg.unique_device_id = f"Google|{os.urandom(16).hex()}"
    msg.language = "en"
    msg.open_id = open_id
    msg.open_id_type = "4"
    msg.login_open_id_type = 4
    msg.access_token = access_token
    msg.login_by = 3
    msg.platform_sdk_id = 2
    msg.origin_platform_type = "4"
    msg.primary_platform_type = "4"
    return encrypt_proto(msg.SerializeToString())

def do_official_major_login(open_id, access_token):
    url = "https://loginbp.ggpolarbear.com/MajorLogin"
    payload = build_major_login_payload(open_id, access_token)
    headers = {
        "User-Agent": "fadai/1.0 (Linux; Android 13; SM-S918B)",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "ReleaseVersion": "OB54"
    }
    try:
        resp = SESSION.post(url, headers=headers, data=payload, verify=False, timeout=6)
        if resp.status_code == 200:
            res = MajoRLoGinrEs_pb2.MajorLoginRes()
            res.ParseFromString(resp.content)
            return res.token
        return None
    except Exception:
        return None

def get_jwt_token_dual_engine(uid, password):
    # 1. Official Direct Login (Fastest)
    open_id, access_token = get_official_garena_token(uid, password)
    if open_id and access_token:
        jwt = do_official_major_login(open_id, access_token)
        if jwt:
            return jwt, "OFFICIAL"

    # 2. High-Speed Fallback Engine
    try:
        url = "https://ff-jwt-gen-api.lovable.app/api/public/token"
        params = {"guest_uid": str(uid).strip(), "guest_password": str(password).strip()}
        resp = SESSION.get(url, params=params, timeout=7)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success") and data.get("token"):
                return data.get("token"), "FALLBACK"
    except Exception:
        pass

    return None, None

def process_single_account(acc):
    uid = str(acc.get('uid', '')).strip()
    pwd = str(acc.get('password', '')).strip()
    if not uid or not pwd:
        return {"uid": uid, "status": "failed", "message": "Missing credentials"}
    
    jwt, engine = get_jwt_token_dual_engine(uid, pwd)
    if jwt:
        return {"uid": uid, "status": "success", "token": jwt, "engine": engine}
    return {"uid": uid, "status": "failed", "message": "Login failed"}

class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        self._send_json(200, {"status": "online", "engine": "Turbo Multi-Threaded Engine Active"})

    def do_POST(self):
        try:
            content_len = int(self.headers.get('Content-Length', 0))
            raw_body = self.rfile.read(content_len)
            data = json.loads(raw_body.decode('utf-8'))

            # 🚀 ব্যাচ সাপোর্ট: একসাথে একাধিক আইডি পাঠানো হলে
            if "accounts" in data and isinstance(data["accounts"], list):
                accounts = data["accounts"]
                # ৩০টি সমান্তরাল থ্রেডে একযোগে জেনারেট হবে
                with ThreadPoolExecutor(max_workers=30) as executor:
                    results = list(executor.map(process_single_account, accounts))
                
                success_count = sum(1 for r in results if r.get("status") == "success")
                self._send_json(200, {
                    "status": "batch_completed",
                    "total": len(accounts),
                    "success": success_count,
                    "results": results
                })
                return

            # একক অ্যাকাউন্টের সাধারণ রিকোয়েস্ট
            uid = str(data.get('uid', '')).strip()
            password = str(data.get('password', '')).strip()

            if not uid or not password:
                self._send_json(400, {"status": "failed", "message": "UID and password required"})
                return

            jwt_token, engine = get_jwt_token_dual_engine(uid, password)
            if jwt_token:
                self._send_json(200, {
                    "status": "success",
                    "uid": uid,
                    "engine": engine,
                    "jwt_token": jwt_token
                })
            else:
                self._send_json(200, {"status": "failed", "uid": uid, "message": "Login failed"})

        except Exception as e:
            self._send_json(500, {"status": "error", "message": str(e)})

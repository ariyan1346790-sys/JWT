import os
import sys
import json
import urllib3
import requests
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Dynamic Pb2 Importer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Pb2'))
try:
    import MajoRLoGinrEq_pb2
    import MajoRLoGinrEs_pb2
except ImportError:
    pass

STATIC_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
STATIC_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
CLIENT_VERSION = "1.126.4"

def encrypt_proto(payload_bytes: bytes) -> bytes:
    cipher = AES.new(STATIC_KEY, AES.MODE_CBC, STATIC_IV)
    return cipher.encrypt(pad(payload_bytes, AES.block_size))

# ================= METHOD 1: OFFICIAL GARENA OAUTH =================
def get_official_garena_token(uid, password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    headers = {
        "Host": "100067.connect.garena.com",
        "User-Agent": "GarenaMSDK/5.5.2P3(SM-A515F;Android 12;en-US;IND;)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "close"
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
        resp = requests.post(url, headers=headers, data=data, verify=False, timeout=8)
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
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "ReleaseVersion": "OB54"
    }
    try:
        resp = requests.post(url, headers=headers, data=payload, verify=False, timeout=8)
        if resp.status_code == 200:
            res = MajoRLoGinrEs_pb2.MajorLoginRes()
            res.ParseFromString(resp.content)
            return res.token
        return None
    except Exception:
        return None

# ================= DUAL ENGINE RUNNER =================
def get_jwt_token_dual_engine(uid, password):
    # Method 1: Direct Official Garena OAuth Chain
    open_id, access_token = get_official_garena_token(uid, password)
    if open_id and access_token:
        jwt = do_official_major_login(open_id, access_token)
        if jwt:
            return jwt, "OFFICIAL_ENGINE"

    # Method 2: High-Speed Dedicated JWT API Fallback
    try:
        url = "https://ff-jwt-gen-api.lovable.app/api/public/token"
        params = {"guest_uid": str(uid).strip(), "guest_password": str(password).strip()}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success") and data.get("token"):
                return data.get("token"), "FALLBACK_ENGINE"
    except Exception:
        pass

    return None, None

# ================= SERVERLESS HANDLER =================
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
        self._send_json(200, {"status": "online", "service": "Garena Dual-Engine Token API v3.0"})

    def do_POST(self):
        try:
            content_len = int(self.headers.get('Content-Length', 0))
            raw_body = self.rfile.read(content_len)
            data = json.loads(raw_body.decode('utf-8'))

            uid = str(data.get('uid', '')).strip()
            password = str(data.get('password', '')).strip()

            if not uid or not password:
                self._send_json(400, {
                    "status": "failed",
                    "result_type": "INVALID_INPUT",
                    "message": "Both UID and Password are required."
                })
                return

            # Run Dual Engine
            jwt_token, engine_used = get_jwt_token_dual_engine(uid, password)

            if jwt_token:
                self._send_json(200, {
                    "status": "success",
                    "result_type": "SUCCESS",
                    "uid": uid,
                    "engine": engine_used,
                    "jwt_token": jwt_token,
                    "message": "Token generated successfully"
                })
            else:
                self._send_json(200, {
                    "status": "failed",
                    "result_type": "LOGIN_FAILED",
                    "uid": uid,
                    "message": "Failed to login or bad credentials"
                })

        except Exception as e:
            self._send_json(500, {
                "status": "error",
                "result_type": "SERVER_ERROR",
                "message": str(e)
            })

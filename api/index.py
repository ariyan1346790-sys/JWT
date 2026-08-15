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

def get_guest_token(uid, password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    headers = {
        "Host": "100067.connect.garena.com",
        "User-Agent": "GarenaMSDK/5.5.2P3(SM-A515F;Android 12;en-US;IND;)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
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
        resp = requests.post(url, headers=headers, data=data, verify=False, timeout=12)
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
    msg.system_software = "Android OS 11 / API-30 (RQ3A.210805.001)"
    msg.system_hardware = "Handheld"
    msg.device_type = "Handheld"
    msg.telecom_operator = "Verizon"
    msg.network_operator_a = "Verizon"
    msg.network_type = "WIFI"
    msg.network_type_a = "WIFI"
    msg.screen_width = 1080
    msg.screen_height = 2400
    msg.screen_dpi = "440"
    msg.processor_details = "ARMv8"
    msg.cpu_type = 2
    msg.cpu_architecture = "64"
    msg.memory = 6144
    msg.gpu_renderer = "Adreno (TM) 650"
    msg.gpu_version = "OpenGL ES 3.2 V@1.50"
    msg.graphics_api = "OpenGLES3"
    msg.unique_device_id = f"Google|{os.urandom(16).hex()}"
    msg.client_ip = ""
    msg.language = "en"
    msg.open_id = open_id
    msg.open_id_type = "4"
    msg.login_open_id_type = 4
    msg.access_token = access_token
    msg.login_by = 3
    msg.platform_sdk_id = 2
    msg.origin_platform_type = "4"
    msg.primary_platform_type = "4"
    msg.memory_available.version = 55
    msg.memory_available.hidden_value = 81
    msg.external_storage_total = 128512
    msg.external_storage_available = 42000
    msg.internal_storage_total = 110731
    msg.internal_storage_available = 25000
    msg.game_disk_storage_total = 26628
    msg.game_disk_storage_available = 22000
    msg.external_sdcard_total_storage = 119234
    msg.external_sdcard_avail_storage = 50000
    msg.library_path = "/data/app/~~random/base.apk"
    msg.library_token = "hash|base.apk"
    msg.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    msg.supported_astc_bitset = 16383
    msg.analytics_detail = b"FwQVTgUPX1UaUllDDwcWCRBpWAUOUgsvA1snWlBaO1kFYg=="
    msg.loading_time = 13564
    msg.release_channel = "android"
    msg.channel_type = 3
    msg.reg_avatar = 1
    msg.if_push = 1
    msg.is_vpn = 0
    msg.android_engine_init_flag = 110009
    return encrypt_proto(msg.SerializeToString())

def do_major_login(encrypted_payload):
    url = "https://loginbp.ggpolarbear.com/MajorLogin"
    headers = {
        "User-Agent": "fadai/1.0 (Linux; Android 13; SM-S918B Build/TP1A.220.624.014)",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB54"
    }
    try:
        resp = requests.post(url, headers=headers, data=encrypted_payload, verify=False, timeout=12)
        if resp.status_code == 200:
            res = MajoRLoGinrEs_pb2.MajorLoginRes()
            res.ParseFromString(resp.content)
            return res.token
        return None
    except Exception:
        return None

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
        self._send_json(200, {"status": "online", "service": "Garena Token Engine API v1.0"})

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

            # Attempt Token Generation (2 Retries)
            jwt_token = None
            for _ in range(2):
                open_id, access_token = get_guest_token(uid, password)
                if open_id and access_token:
                    payload = build_major_login_payload(open_id, access_token)
                    jwt_token = do_major_login(payload)
                    if jwt_token:
                        break

            if jwt_token:
                self._send_json(200, {
                    "status": "success",
                    "result_type": "SUCCESS",
                    "uid": uid,
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

from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_ROOT.parent

SECRET_KEY = "asl_sign_language_secret"
HOST = "0.0.0.0"
PORT = 5000

CERT_PATH = APP_ROOT / "cert.pem"
KEY_PATH = APP_ROOT / "key.pem"

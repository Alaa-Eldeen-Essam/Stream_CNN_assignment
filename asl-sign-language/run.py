from app import create_app
from app.config import CERT_PATH, HOST, KEY_PATH, PORT
from app.extensions import socketio
from app.utils.logging_utils import get_logger

log = get_logger(__name__)


def run_server():
    try:
        flask_app = create_app()
    except RuntimeError as exc:
        log.error(str(exc))
        raise SystemExit(1) from exc

    ssl_context = None
    if CERT_PATH.exists() and KEY_PATH.exists():
        ssl_context = (str(CERT_PATH), str(KEY_PATH))
        log.info("HTTPS enabled - open https://127.0.0.1:5000")
    else:
        log.warning("cert.pem/key.pem not found - running HTTP on localhost")
        log.info("Listening on http://127.0.0.1:5000")

    socketio.run(flask_app, host=HOST, port=PORT, ssl_context=ssl_context, debug=False)


if __name__ == "__main__":
    run_server()

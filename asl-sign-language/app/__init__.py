from flask import Flask

from app.config import APP_ROOT, SECRET_KEY
from app.domain.model_registry import DEFAULT_MODEL
from app.extensions import socketio
from app.routes.socket_handlers import register_socket_handlers
from app.routes.web import web_bp
from app.services.hand_detection_service import HandDetectionService
from app.services.inference_service import InferenceService
from app.services.model_service import ModelService
from app.utils.logging_utils import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)


def create_app():
    app = Flask(
        __name__,
        template_folder=str(APP_ROOT / "templates"),
        static_folder=str(APP_ROOT / "static"),
    )
    app.config["SECRET_KEY"] = SECRET_KEY

    model_service = ModelService(log)
    hand_detection_service = HandDetectionService()
    inference_service = InferenceService(model_service, hand_detection_service)

    model_service.discover_model_paths()
    if not model_service.available_model_paths:
        raise RuntimeError("No models loaded. Place .h5 files beside server_cnn.py or in ../models.")

    default_key, _ = model_service.load_model_if_needed(DEFAULT_MODEL)
    if default_key is None:
        raise RuntimeError("Failed to load a default model.")

    app.config["MODEL_SERVICE"] = model_service
    app.config["HAND_DETECTION_SERVICE"] = hand_detection_service
    app.config["INFERENCE_SERVICE"] = inference_service

    app.register_blueprint(web_bp)
    socketio.init_app(app)
    register_socket_handlers(socketio)

    log.info(f"Available models: {model_service.get_available_models()}")
    return app

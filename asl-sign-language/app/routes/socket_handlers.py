from flask import current_app, request
from flask_socketio import emit

from app.domain.model_registry import DEFAULT_MODEL
from app.domain.prediction_state import NO_HAND
from app.domain.response_builder import build_prediction_response
from app.services.frame_service import decode_frame


def register_socket_handlers(socketio):
    @socketio.on("disconnect")
    def handle_disconnect():
        current_app.config["INFERENCE_SERVICE"].clear_client(request.sid)

    @socketio.on("video_frame")
    def handle_video_frame(data):
        frame = decode_frame(data)
        requested_model = data.get("model", DEFAULT_MODEL) if isinstance(data, dict) else DEFAULT_MODEL
        hand_connections = current_app.config["HAND_DETECTION_SERVICE"].connections

        if frame is None:
            emit("prediction", build_prediction_response(requested_model, NO_HAND, hand_connections))
            return

        result = current_app.config["INFERENCE_SERVICE"].run_prediction(
            frame,
            requested_model,
            request.sid,
        )
        emit("prediction", result)

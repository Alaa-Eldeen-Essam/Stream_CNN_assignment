"""
server_cnn.py - ASL Sign Language Real-Time Prediction Server

Local demo behavior:
- MediaPipe must detect one valid hand before CNN inference runs.
- The browser renders the 21 MediaPipe landmarks plus hand connections.
- Predictions are smoothed conservatively to avoid false positives.
"""

import base64
import logging
import threading
import warnings
from collections import Counter, defaultdict, deque
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from tensorflow.keras import applications

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="[server] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DEFAULT_MODEL = "mobilenetv2"
MIN_BOX_SIDE_RATIO = 0.12
PREDICTION_THRESHOLD = 75.0
TOP2_MARGIN_THRESHOLD = 18.0
SMOOTHING_WINDOW = 4
SMOOTHING_MIN_AGREEMENT = 3


def resolve_asset_path(filename):
    """Resolve assets from the app folder or the repo-level models folder."""
    candidates = (
        BASE_DIR / filename,
        BASE_DIR / "models" / filename,
        PROJECT_ROOT / "models" / filename,
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


def create_hands_components():
    """Support both legacy `mp.solutions` and direct solution imports."""
    try:
        mp_hands = mp.solutions.hands
    except AttributeError:
        try:
            from mediapipe.python.solutions import hands as mp_hands
        except ImportError as exc:
            raise RuntimeError(
                "This project uses MediaPipe legacy Hands. Install a MediaPipe build "
                "that still includes `mediapipe.python.solutions.hands`."
            ) from exc

    detector = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.55,
        min_tracking_confidence=0.5,
    )
    connections = [list(edge) for edge in mp_hands.HAND_CONNECTIONS]
    return detector, connections


ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
IDX_TO_LETTER = {i: c for i, c in enumerate(c for c in ALPHABET if c not in ("J", "Z"))}

MODEL_REGISTRY = {
    "alexnet": {
        "file": "alexnet_sign.h5",
        "input_size": (227, 227),
        "color": "rgb",
        "preprocess": None,
        "live_enabled": True,
    },
    "resnet50": {
        "file": "resnet50_sign.h5",
        "input_size": (224, 224),
        "color": "rgb",
        "preprocess": applications.resnet50.preprocess_input,
        "live_enabled": False,
    },
    "vgg16": {
        "file": "vgg16_sign.h5",
        "input_size": (224, 224),
        "color": "rgb",
        "preprocess": applications.vgg16.preprocess_input,
        "live_enabled": False,
    },
    "mobilenetv2": {
        "file": "mobilenetv2_sign.h5",
        "input_size": (96, 96),
        "color": "rgb",
        "preprocess": applications.mobilenet_v2.preprocess_input,
        "live_enabled": True,
    },
    "efficientnetb0": {
        "file": "efficientnetb0_sign.h5",
        "input_size": (224, 224),
        "color": "rgb",
        "preprocess": None,
        "live_enabled": True,
    },
}

hands_detector, HAND_CONNECTIONS = create_hands_components()
loaded_models = {}
available_model_paths = {}
prediction_histories = defaultdict(lambda: deque(maxlen=SMOOTHING_WINDOW))
model_load_locks = defaultdict(threading.Lock)


def discover_model_paths():
    """Collect only model files that actually exist on disk."""
    discovered = {}
    for key, cfg in MODEL_REGISTRY.items():
        path = resolve_asset_path(cfg["file"])
        if path.exists():
            discovered[key] = path
        else:
            log.warning(f"Missing .h5 file: {path} - skipping '{key}'")
    return discovered


def get_available_models():
    preferred = [
        DEFAULT_MODEL
        if DEFAULT_MODEL in available_model_paths and MODEL_REGISTRY[DEFAULT_MODEL].get("live_enabled", True)
        else None
    ]
    others = [
        key
        for key in MODEL_REGISTRY
        if key in available_model_paths
        and key != DEFAULT_MODEL
        and MODEL_REGISTRY[key].get("live_enabled", True)
    ]
    preferred = [key for key in preferred if key]
    return preferred + others


def load_model_if_needed(model_key):
    """Load a model on demand and cache it for future requests."""
    key = (
        model_key
        if model_key in available_model_paths and MODEL_REGISTRY[model_key].get("live_enabled", True)
        else None
    )
    if key is None:
        available = get_available_models()
        if not available:
            return None, None
        key = DEFAULT_MODEL if DEFAULT_MODEL in available else available[0]

    if key not in loaded_models:
        with model_load_locks[key]:
            if key not in loaded_models:
                path = available_model_paths[key]
                log.info(f"Loading model: {key:<18} from {path}")
                try:
                    loaded_models[key] = tf.keras.models.load_model(path)
                    log.info(f"  + {key} - input shape: {loaded_models[key].input_shape}")
                except Exception as exc:
                    log.warning(f"  x {key} failed to load: {exc}")
                    available_model_paths.pop(key, None)
                    return None, None

    return key, loaded_models[key]


def serialize_landmarks(landmarks):
    return [{"x": float(lm.x), "y": float(lm.y)} for lm in landmarks.landmark]


def crop_relative_points(landmarks, x1, y1, frame_h, frame_w):
    points = []
    for lm in landmarks.landmark:
        px = int(round(lm.x * frame_w)) - x1
        py = int(round(lm.y * frame_h)) - y1
        points.append((px, py))
    return points


def get_hand_bbox(landmarks, frame_h, frame_w, pad=20):
    xs = [lm.x * frame_w for lm in landmarks.landmark]
    ys = [lm.y * frame_h for lm in landmarks.landmark]
    x1 = max(0, int(min(xs)) - pad)
    y1 = max(0, int(min(ys)) - pad)
    x2 = min(frame_w, int(max(xs)) + pad)
    y2 = min(frame_h, int(max(ys)) + pad)
    return x1, y1, x2, y2


def is_valid_bbox(x1, y1, x2, y2, frame_h, frame_w):
    box_w = x2 - x1
    box_h = y2 - y1
    if box_w <= 0 or box_h <= 0:
        return False
    return box_w >= frame_w * MIN_BOX_SIDE_RATIO and box_h >= frame_h * MIN_BOX_SIDE_RATIO


def normalize_bbox(x1, y1, x2, y2, frame_h, frame_w):
    return {
        "x1": round(x1 / frame_w, 4),
        "y1": round(y1 / frame_h, 4),
        "x2": round(x2 / frame_w, 4),
        "y2": round(y2 / frame_h, 4),
    }


def detect_hand(frame_bgr):
    frame_h, frame_w = frame_bgr.shape[:2]
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    result = hands_detector.process(rgb)

    if not result.multi_hand_landmarks or len(result.multi_hand_landmarks) != 1:
        return None

    landmarks = result.multi_hand_landmarks[0]
    x1, y1, x2, y2 = get_hand_bbox(landmarks, frame_h, frame_w)
    if not is_valid_bbox(x1, y1, x2, y2, frame_h, frame_w):
        return None

    crop = frame_bgr[y1:y2, x1:x2]
    if crop.size == 0:
        return None

    hand_points = crop_relative_points(landmarks, x1, y1, frame_h, frame_w)

    return {
        "crop": crop,
        "hand_points": hand_points,
        "landmarks": serialize_landmarks(landmarks),
        "bbox": normalize_bbox(x1, y1, x2, y2, frame_h, frame_w),
    }


def build_hand_mask(shape, hand_points):
    crop_h, crop_w = shape[:2]
    mask = np.zeros((crop_h, crop_w), dtype=np.uint8)
    if not hand_points:
        return mask

    points = np.array(
        [
            [np.clip(px, 0, crop_w - 1), np.clip(py, 0, crop_h - 1)]
            for px, py in hand_points
        ],
        dtype=np.int32,
    )
    if len(points) >= 3:
        hull = cv2.convexHull(points)
        cv2.fillConvexPoly(mask, hull, 255)

    scale = max(crop_h, crop_w)
    line_thickness = max(4, int(scale * 0.05))
    joint_radius = max(4, int(scale * 0.035))
    dilation = max(3, int(scale * 0.04))

    for start_idx, end_idx in HAND_CONNECTIONS:
        start = tuple(points[start_idx])
        end = tuple(points[end_idx])
        cv2.line(mask, start, end, 255, thickness=line_thickness)

    for point in points:
        cv2.circle(mask, tuple(point), joint_radius, 255, thickness=-1)

    kernel = np.ones((dilation, dilation), dtype=np.uint8)
    return cv2.dilate(mask, kernel, iterations=1)


def preprocess_crop(crop_bgr, hand_points, model_key):
    cfg = MODEL_REGISTRY[model_key]
    target_w, target_h = cfg["input_size"]

    gray_crop = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    hand_mask = build_hand_mask(crop_bgr.shape, hand_points)
    masked_gray = cv2.bitwise_and(gray_crop, gray_crop, mask=hand_mask)
    resized_gray = cv2.resize(masked_gray, (target_w, target_h))
    resized = np.stack([resized_gray, resized_gray, resized_gray], axis=-1)
    inp = resized.reshape(1, target_h, target_w, 3).astype("float32")

    if model_key == "efficientnetb0":
        return inp, masked_gray
    if cfg["preprocess"] is not None:
        return cfg["preprocess"](inp), masked_gray
    return inp / 255.0, masked_gray


def top_predictions(preds, limit=3):
    top_indices = np.argsort(preds)[::-1][:limit]
    return [
        {"label": IDX_TO_LETTER.get(int(idx), "?"), "confidence": round(float(preds[idx]) * 100, 1)}
        for idx in top_indices
    ]


def encode_preview_image(image):
    success, buf = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not success:
        return ""
    return f"data:image/jpeg;base64,{base64.b64encode(buf.tobytes()).decode('ascii')}"


def base_response(
    model_key,
    state,
    hand_detected=False,
    landmarks=None,
    bbox=None,
    label="",
    confidence=0.0,
    top_scores=None,
    rejection_reason="",
    masked_preview="",
):
    return {
        "state": state,
        "label": label,
        "confidence": round(float(confidence), 1),
        "model": model_key,
        "hand_detected": hand_detected,
        "landmarks": landmarks or [],
        "connections": HAND_CONNECTIONS if landmarks else [],
        "bbox": bbox,
        "top_scores": top_scores or [],
        "rejection_reason": rejection_reason,
        "masked_preview": masked_preview,
    }


def stable_prediction(history):
    if len(history) < SMOOTHING_MIN_AGREEMENT:
        return None

    labels = [label for label, _ in history]
    label, count = Counter(labels).most_common(1)[0]
    if count < SMOOTHING_MIN_AGREEMENT:
        return None

    confidences = [conf for hist_label, conf in history if hist_label == label]
    avg_conf = sum(confidences) / len(confidences)
    return label, avg_conf


def run_prediction(frame_bgr, requested_model, client_id):
    model_key, model = load_model_if_needed(requested_model)
    if model is None:
        return base_response(requested_model or DEFAULT_MODEL, "no_hand")

    detection = detect_hand(frame_bgr)
    if detection is None:
        prediction_histories[client_id].clear()
        return base_response(model_key, "no_hand")

    inp, masked_gray = preprocess_crop(detection["crop"], detection["hand_points"], model_key)
    preds = model.predict(inp, verbose=0)
    sorted_indices = np.argsort(preds[0])[::-1]
    idx = int(sorted_indices[0])
    conf = float(preds[0][idx]) * 100
    label = IDX_TO_LETTER.get(idx, "?")
    second_conf = float(preds[0][sorted_indices[1]]) * 100 if len(sorted_indices) > 1 else 0.0
    margin = conf - second_conf
    top_scores = top_predictions(preds[0])
    masked_preview = encode_preview_image(masked_gray)

    history = prediction_histories[client_id]
    history.append((label, conf))
    stable = stable_prediction(history)

    rejection_reason = ""
    if conf < PREDICTION_THRESHOLD:
        rejection_reason = "Low confidence"
    elif margin < TOP2_MARGIN_THRESHOLD:
        rejection_reason = "Top-2 margin too small"
    elif stable is None:
        rejection_reason = "Waiting for stable frames"

    if rejection_reason:
        return base_response(
            model_key,
            "unsure",
            hand_detected=True,
            landmarks=detection["landmarks"],
            bbox=detection["bbox"],
            label=label,
            confidence=conf,
            top_scores=top_scores,
            rejection_reason=rejection_reason,
            masked_preview=masked_preview,
        )

    stable_label, stable_conf = stable
    return base_response(
        model_key,
        "predicted",
        hand_detected=True,
        landmarks=detection["landmarks"],
        bbox=detection["bbox"],
        label=stable_label,
        confidence=stable_conf,
        top_scores=top_scores,
        masked_preview=masked_preview,
    )


app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = "asl_sign_language_secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


@app.route("/")
def index():
    models = get_available_models()
    return render_template(
        "index.html",
        models=models,
        default_model=DEFAULT_MODEL if DEFAULT_MODEL in models else (models[0] if models else ""),
    )


@socketio.on("disconnect")
def handle_disconnect():
    prediction_histories.pop(request.sid, None)


@socketio.on("video_frame")
def handle_video_frame(data):
    b64 = data["frame"].split(",", 1)[1]
    buf = np.frombuffer(base64.b64decode(b64), dtype=np.uint8)
    frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if frame is None:
        emit("prediction", base_response(data.get("model", DEFAULT_MODEL), "no_hand"))
        return

    result = run_prediction(frame, data.get("model", DEFAULT_MODEL), request.sid)
    emit("prediction", result)


if __name__ == "__main__":
    available_model_paths = discover_model_paths()
    if not available_model_paths:
        log.error("No models loaded. Place .h5 files beside server_cnn.py or in ../models.")
        raise SystemExit(1)

    default_key, _ = load_model_if_needed(DEFAULT_MODEL)
    if default_key is None:
        log.error("Failed to load a default model.")
        raise SystemExit(1)

    log.info(f"Available models: {get_available_models()}")

    ssl_context = None
    cert_path = BASE_DIR / "cert.pem"
    key_path = BASE_DIR / "key.pem"
    if cert_path.exists() and key_path.exists():
        ssl_context = (str(cert_path), str(key_path))
        log.info("HTTPS enabled - open https://127.0.0.1:5000")
    else:
        log.warning("cert.pem/key.pem not found - running HTTP on localhost")
        log.info("Listening on http://127.0.0.1:5000")

    socketio.run(app, host="0.0.0.0", port=5000, ssl_context=ssl_context, debug=False)

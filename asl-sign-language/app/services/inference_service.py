from collections import Counter, defaultdict, deque

import cv2
import numpy as np

from app.domain.model_registry import (
    DEFAULT_MODEL,
    IDX_TO_LETTER,
    MODEL_REGISTRY,
    PREDICTION_THRESHOLD,
    SMOOTHING_MIN_AGREEMENT,
    SMOOTHING_WINDOW,
    TOP2_MARGIN_THRESHOLD,
)
from app.domain.prediction_state import NO_HAND, PREDICTED, UNSURE
from app.domain.response_builder import build_prediction_response
from app.utils.image_utils import encode_preview_image


class InferenceService:
    def __init__(self, model_service, hand_detection_service):
        self.model_service = model_service
        self.hand_detection_service = hand_detection_service
        self.prediction_histories = defaultdict(lambda: deque(maxlen=SMOOTHING_WINDOW))

    def clear_client(self, client_id):
        self.prediction_histories.pop(client_id, None)

    def run_prediction(self, frame_bgr, requested_model, client_id):
        model_key, model = self.model_service.load_model_if_needed(requested_model)
        if model is None:
            return self._response(requested_model or DEFAULT_MODEL, NO_HAND)

        detection = self.hand_detection_service.detect_hand(frame_bgr)
        if detection is None:
            self.prediction_histories[client_id].clear()
            return self._response(model_key, NO_HAND)

        inp, masked_gray = self._preprocess_crop(detection["crop"], detection["hand_points"], model_key)
        preds = model.predict(inp, verbose=0)
        sorted_indices = np.argsort(preds[0])[::-1]
        idx = int(sorted_indices[0])
        conf = float(preds[0][idx]) * 100
        label = IDX_TO_LETTER.get(idx, "?")
        second_conf = float(preds[0][sorted_indices[1]]) * 100 if len(sorted_indices) > 1 else 0.0
        margin = conf - second_conf
        top_scores = self._top_predictions(preds[0])
        masked_preview = encode_preview_image(masked_gray)

        history = self.prediction_histories[client_id]
        history.append((label, conf))
        stable = self._stable_prediction(history)

        rejection_reason = ""
        if conf < PREDICTION_THRESHOLD:
            rejection_reason = "Low confidence"
        elif margin < TOP2_MARGIN_THRESHOLD:
            rejection_reason = "Top-2 margin too small"
        elif stable is None:
            rejection_reason = "Waiting for stable frames"

        if rejection_reason:
            return self._response(
                model_key,
                UNSURE,
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
        return self._response(
            model_key,
            PREDICTED,
            hand_detected=True,
            landmarks=detection["landmarks"],
            bbox=detection["bbox"],
            label=stable_label,
            confidence=stable_conf,
            top_scores=top_scores,
            masked_preview=masked_preview,
        )

    def _response(self, model_key, state, **kwargs):
        return build_prediction_response(
            model_key,
            state,
            self.hand_detection_service.connections,
            **kwargs,
        )

    def _preprocess_crop(self, crop_bgr, hand_points, model_key):
        cfg = MODEL_REGISTRY[model_key]
        target_w, target_h = cfg["input_size"]

        gray_crop = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
        hand_mask = self._build_hand_mask(crop_bgr.shape, hand_points)
        masked_gray = cv2.bitwise_and(gray_crop, gray_crop, mask=hand_mask)
        resized_gray = cv2.resize(masked_gray, (target_w, target_h))
        resized = np.stack([resized_gray, resized_gray, resized_gray], axis=-1)
        inp = resized.reshape(1, target_h, target_w, 3).astype("float32")

        if model_key == "efficientnetb0":
            return inp, masked_gray
        if cfg["preprocess"] is not None:
            return cfg["preprocess"](inp), masked_gray
        return inp / 255.0, masked_gray

    def _build_hand_mask(self, shape, hand_points):
        crop_h, crop_w = shape[:2]
        mask = np.zeros((crop_h, crop_w), dtype=np.uint8)
        if not hand_points:
            return mask

        points = np.array(
            [[np.clip(px, 0, crop_w - 1), np.clip(py, 0, crop_h - 1)] for px, py in hand_points],
            dtype=np.int32,
        )
        if len(points) >= 3:
            hull = cv2.convexHull(points)
            cv2.fillConvexPoly(mask, hull, 255)

        scale = max(crop_h, crop_w)
        line_thickness = max(4, int(scale * 0.05))
        joint_radius = max(4, int(scale * 0.035))
        dilation = max(3, int(scale * 0.04))

        for start_idx, end_idx in self.hand_detection_service.connections:
            start = tuple(points[start_idx])
            end = tuple(points[end_idx])
            cv2.line(mask, start, end, 255, thickness=line_thickness)

        for point in points:
            cv2.circle(mask, tuple(point), joint_radius, 255, thickness=-1)

        kernel = np.ones((dilation, dilation), dtype=np.uint8)
        return cv2.dilate(mask, kernel, iterations=1)

    def _top_predictions(self, preds, limit=3):
        top_indices = np.argsort(preds)[::-1][:limit]
        return [
            {
                "label": IDX_TO_LETTER.get(int(idx), "?"),
                "confidence": round(float(preds[idx]) * 100, 1),
            }
            for idx in top_indices
        ]

    def _stable_prediction(self, history):
        if len(history) < SMOOTHING_MIN_AGREEMENT:
            return None

        labels = [label for label, _ in history]
        label, count = Counter(labels).most_common(1)[0]
        if count < SMOOTHING_MIN_AGREEMENT:
            return None

        confidences = [conf for hist_label, conf in history if hist_label == label]
        avg_conf = sum(confidences) / len(confidences)
        return label, avg_conf

import cv2
import mediapipe as mp

from app.domain.model_registry import MIN_BOX_SIDE_RATIO


class HandDetectionService:
    def __init__(self):
        self.detector, self.connections = self._create_hands_components()

    def _create_hands_components(self):
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

    def detect_hand(self, frame_bgr):
        frame_h, frame_w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self.detector.process(rgb)

        if not result.multi_hand_landmarks or len(result.multi_hand_landmarks) != 1:
            return None

        landmarks = result.multi_hand_landmarks[0]
        x1, y1, x2, y2 = self._get_hand_bbox(landmarks, frame_h, frame_w)
        if not self._is_valid_bbox(x1, y1, x2, y2, frame_h, frame_w):
            return None

        crop = frame_bgr[y1:y2, x1:x2]
        if crop.size == 0:
            return None

        return {
            "crop": crop,
            "hand_points": self._crop_relative_points(landmarks, x1, y1, frame_h, frame_w),
            "landmarks": self._serialize_landmarks(landmarks),
            "bbox": self._normalize_bbox(x1, y1, x2, y2, frame_h, frame_w),
        }

    def _serialize_landmarks(self, landmarks):
        return [{"x": float(lm.x), "y": float(lm.y)} for lm in landmarks.landmark]

    def _crop_relative_points(self, landmarks, x1, y1, frame_h, frame_w):
        points = []
        for lm in landmarks.landmark:
            px = int(round(lm.x * frame_w)) - x1
            py = int(round(lm.y * frame_h)) - y1
            points.append((px, py))
        return points

    def _get_hand_bbox(self, landmarks, frame_h, frame_w, pad=20):
        xs = [lm.x * frame_w for lm in landmarks.landmark]
        ys = [lm.y * frame_h for lm in landmarks.landmark]
        x1 = max(0, int(min(xs)) - pad)
        y1 = max(0, int(min(ys)) - pad)
        x2 = min(frame_w, int(max(xs)) + pad)
        y2 = min(frame_h, int(max(ys)) + pad)
        return x1, y1, x2, y2

    def _is_valid_bbox(self, x1, y1, x2, y2, frame_h, frame_w):
        box_w = x2 - x1
        box_h = y2 - y1
        if box_w <= 0 or box_h <= 0:
            return False
        return box_w >= frame_w * MIN_BOX_SIDE_RATIO and box_h >= frame_h * MIN_BOX_SIDE_RATIO

    def _normalize_bbox(self, x1, y1, x2, y2, frame_h, frame_w):
        return {
            "x1": round(x1 / frame_w, 4),
            "y1": round(y1 / frame_h, 4),
            "x2": round(x2 / frame_w, 4),
            "y2": round(y2 / frame_h, 4),
        }

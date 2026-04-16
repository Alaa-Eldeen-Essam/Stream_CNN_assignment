import base64

import cv2
import numpy as np


def decode_frame(data):
    try:
        frame_data = data["frame"]
        b64 = frame_data.split(",", 1)[1]
        buf = np.frombuffer(base64.b64decode(b64), dtype=np.uint8)
    except (KeyError, IndexError, TypeError, ValueError):
        return None
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)

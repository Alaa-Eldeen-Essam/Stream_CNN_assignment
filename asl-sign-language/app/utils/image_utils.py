import base64

import cv2


def encode_preview_image(image):
    success, buf = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not success:
        return ""
    return f"data:image/jpeg;base64,{base64.b64encode(buf.tobytes()).decode('ascii')}"

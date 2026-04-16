# ASL Sign Language Recognition

Local live demo for static ASL letter recognition using MediaPipe hand detection, CNN classifiers, Flask, and Socket.IO.

## Current Demo Behavior

- MediaPipe is mandatory for inference. If no valid hand is detected, the CNN does not run.
- The browser shows the 21 MediaPipe landmarks, hand connections, and the detected hand box.
- The webcam preview is mirrored for a natural selfie view.
- The detected hand crop is converted to grayscale and background-masked from the MediaPipe landmarks before inference.
- Predictions are conservative:
  - `No hand` when MediaPipe finds nothing usable
  - `Unsure` when the model is not stable/confident enough
  - a letter only after a valid hand crop and smoothed agreement
- Live predictions also use a top-2 margin rejection rule to suppress ambiguous letters.
- The UI includes an optional debug panel with the top-3 class scores and rejection reason.
- The app is optimized for one-hand static letters only.
- `J` and `Z` are intentionally unsupported because they require motion.

## Project Structure

```text
Stream_CNN_assignment/
├── asl-sign-language/
│   ├── server_cnn.py
│   ├── requirements.txt
│   ├── static/
│   │   ├── app.js
│   │   └── styles.css
│   └── templates/
│       └── index.html
├── models/
│   ├── alexnet_sign.h5
│   ├── resnet50_sign.h5
│   ├── vgg16_sign.h5
│   ├── mobilenetv2_sign.h5
│   └── efficientnetb0_sign.h5
└── Notebooks/
    └── ASL_Sign_Language_CNN_Alaa.ipynb
```

`mobilenetv2` is the default live model because it offers the best responsiveness for localhost demo use. Only the stronger live-demo models are exposed in the selector; weak or unstable models are hidden from the UI.

## Quick Start

```bash
cd asl-sign-language
pip install -r requirements.txt
python server_cnn.py
```

Open `http://127.0.0.1:5000`.

If you want HTTPS for non-localhost browser access, place `cert.pem` and `key.pem` inside `asl-sign-language/`.

## Inference Pipeline

```text
webcam frame
    ↓
MediaPipe Hands
    ↓
validate one hand + bounding box size
    ↓
crop detected hand only
    ↓
landmark-based background mask
    ↓
grayscale-aligned preprocessing
    ↓
CNN inference
    ↓
confidence + top-2 margin + smoothing gate
    ↓
No hand / Unsure / Predicted letter
```

Important rule: no MediaPipe hand detection means no CNN inference.

## Live Streaming Notes

- Transport is currently Socket.IO polling on top of Flask-SocketIO threading mode.
- This is intentional for low-risk localhost demo stability.
- The browser sends JPEG frames every 200 ms and receives structured prediction events.

Prediction payload fields:

- `state`: `no_hand`, `unsure`, or `predicted`
- `label`
- `confidence`
- `model`
- `hand_detected`
- `landmarks`
- `connections`
- `bbox`
- `top_scores`
- `rejection_reason`

## Known Limitations

- Best results require one clear hand in frame.
- Busy backgrounds, poor lighting, and partial hands reduce stability.
- The demo is optimized for localhost and a laptop webcam, not production deployment.
- Models are lazy-loaded after startup except for the default model.
- Background masking helps, but the models are still trained on Sign Language MNIST style data rather than true webcam data.

## Requirements

See [asl-sign-language/requirements.txt](./asl-sign-language/requirements.txt).

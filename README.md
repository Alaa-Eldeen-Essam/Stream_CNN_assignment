# ASL Sign Language Recognition

Local live demo for static ASL letter recognition using MediaPipe hand detection, CNN classifiers, Flask, and Socket.IO.

## Current Demo Behavior

- MediaPipe is mandatory for inference. If no valid hand is detected, the CNN does not run.
- The browser shows the 21 MediaPipe landmarks, hand connections, and the detected hand box.
- The webcam preview is mirrored for a natural selfie view.
- The detected hand crop is converted to grayscale and background-masked from the MediaPipe landmarks before inference.
- Predictions are conservative: `No hand`, `Unsure`, or a letter only after a valid hand crop and smoothed agreement.
- Live predictions use confidence, top-2 margin, and temporal smoothing rejection rules.
- The debug panel shows the top-3 class scores, rejection reason, and an optional masked crop preview.
- The app is optimized for one-hand static letters only.
- `J` and `Z` are intentionally unsupported because they require motion.

## Project Structure

```text
Stream_CNN_assignment/
|-- asl-sign-language/
|   |-- run.py
|   |-- server_cnn.py
|   |-- requirements.txt
|   |-- app/
|   |   |-- __init__.py
|   |   |-- config.py
|   |   |-- extensions.py
|   |   |-- routes/
|   |   |-- services/
|   |   |-- domain/
|   |   `-- utils/
|   |-- static/
|   |   |-- app.js
|   |   `-- styles.css
|   `-- templates/
|       `-- index.html
|-- models/
|   |-- alexnet_sign.h5
|   |-- resnet50_sign.h5
|   |-- vgg16_sign.h5
|   |-- mobilenetv2_sign.h5
|   `-- efficientnetb0_sign.h5
`-- Notebooks/
    `-- ASL_Sign_Language_CNN_Alaa.ipynb
```

The backend now follows a pragmatic Flask MVC-style layout:

- Controllers live in `app/routes/`.
- Views live in `templates/` and `static/`.
- Runtime services live in `app/services/`.
- Model registry, prediction states, and response payload construction live in `app/domain/`.
- Small shared helpers live in `app/utils/`.

`server_cnn.py` is kept as a compatibility entrypoint. The preferred entrypoint is `run.py`.

## Quick Start

```bash
cd asl-sign-language
pip install -r requirements.txt
python run.py
```

The legacy command still works:

```bash
python server_cnn.py
```

Open `http://127.0.0.1:5000`.

If you want HTTPS for non-localhost browser access, place `cert.pem` and `key.pem` inside `asl-sign-language/`.

## Inference Pipeline

```text
webcam frame
    |
    v
MediaPipe Hands
    |
    v
validate one hand + bounding box size
    |
    v
crop detected hand only
    |
    v
landmark-based background mask
    |
    v
grayscale-aligned preprocessing
    |
    v
CNN inference
    |
    v
confidence + top-2 margin + smoothing gate
    |
    v
No hand / Unsure / Predicted letter
```

Important rule: no MediaPipe hand detection means no CNN inference.

## Live Streaming Notes

- Transport is currently Socket.IO polling on top of Flask-SocketIO threading mode.
- This is intentional for low-risk localhost demo stability.
- The browser sends JPEG frames every 200 ms and receives structured prediction events.
- `mobilenetv2` is the default live model. Only stronger live-demo models are shown in the selector.

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
- `masked_preview`

## Architecture Notes

- `ModelService` discovers model files, filters live-enabled models, lazy-loads models, and protects loading with per-model locks.
- `HandDetectionService` owns MediaPipe setup, one-hand detection, landmark serialization, and bounding-box validation.
- `InferenceService` owns masking, preprocessing, model prediction, smoothing, top-2 rejection, and response assembly.
- Socket.IO handlers remain thin and only decode frames, delegate to services, and emit prediction payloads.
- The refactor is structural only; routes, event names, payload fields, and UI behavior are intentionally preserved.

## Known Limitations

- Best results require one clear hand in frame.
- Busy backgrounds, poor lighting, and partial hands reduce stability.
- The demo is optimized for localhost and a laptop webcam, not production deployment.
- Models are lazy-loaded after startup except for the default model.
- Background masking helps, but the models are still trained on Sign Language MNIST style data rather than true webcam data.

## Requirements

See [asl-sign-language/requirements.txt](./asl-sign-language/requirements.txt).

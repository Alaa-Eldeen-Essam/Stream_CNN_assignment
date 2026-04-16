from tensorflow.keras import applications

DEFAULT_MODEL = "mobilenetv2"
MIN_BOX_SIDE_RATIO = 0.12
PREDICTION_THRESHOLD = 75.0
TOP2_MARGIN_THRESHOLD = 18.0
SMOOTHING_WINDOW = 4
SMOOTHING_MIN_AGREEMENT = 3

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

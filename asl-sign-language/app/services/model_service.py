import threading
from collections import defaultdict

import tensorflow as tf

from app.domain.model_registry import DEFAULT_MODEL, MODEL_REGISTRY
from app.utils.path_utils import resolve_asset_path


class ModelService:
    def __init__(self, logger):
        self.log = logger
        self.available_model_paths = {}
        self.loaded_models = {}
        self.model_load_locks = defaultdict(threading.Lock)

    def discover_model_paths(self):
        """Collect only model files that actually exist on disk."""
        discovered = {}
        for key, cfg in MODEL_REGISTRY.items():
            path = resolve_asset_path(cfg["file"])
            if path.exists():
                discovered[key] = path
            else:
                self.log.warning(f"Missing .h5 file: {path} - skipping '{key}'")
        self.available_model_paths = discovered
        return discovered

    def get_available_models(self):
        preferred = [
            DEFAULT_MODEL
            if DEFAULT_MODEL in self.available_model_paths
            and MODEL_REGISTRY[DEFAULT_MODEL].get("live_enabled", True)
            else None
        ]
        others = [
            key
            for key in MODEL_REGISTRY
            if key in self.available_model_paths
            and key != DEFAULT_MODEL
            and MODEL_REGISTRY[key].get("live_enabled", True)
        ]
        preferred = [key for key in preferred if key]
        return preferred + others

    def load_model_if_needed(self, model_key):
        """Load a model on demand and cache it for future requests."""
        key = (
            model_key
            if model_key in self.available_model_paths
            and MODEL_REGISTRY[model_key].get("live_enabled", True)
            else None
        )
        if key is None:
            available = self.get_available_models()
            if not available:
                return None, None
            key = DEFAULT_MODEL if DEFAULT_MODEL in available else available[0]

        if key not in self.loaded_models:
            with self.model_load_locks[key]:
                if key not in self.loaded_models:
                    path = self.available_model_paths[key]
                    self.log.info(f"Loading model: {key:<18} from {path}")
                    try:
                        self.loaded_models[key] = tf.keras.models.load_model(path)
                        self.log.info(f"  + {key} - input shape: {self.loaded_models[key].input_shape}")
                    except Exception as exc:
                        self.log.warning(f"  x {key} failed to load: {exc}")
                        self.available_model_paths.pop(key, None)
                        return None, None

        return key, self.loaded_models[key]

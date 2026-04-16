from flask import Blueprint, current_app, render_template

from app.domain.model_registry import DEFAULT_MODEL

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def index():
    model_service = current_app.config["MODEL_SERVICE"]
    models = model_service.get_available_models()
    return render_template(
        "index.html",
        models=models,
        default_model=DEFAULT_MODEL if DEFAULT_MODEL in models else (models[0] if models else ""),
    )

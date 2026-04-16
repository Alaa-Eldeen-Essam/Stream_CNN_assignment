from app.config import APP_ROOT, PROJECT_ROOT


def resolve_asset_path(filename):
    """Resolve assets from the app folder or the repo-level models folder."""
    candidates = (
        APP_ROOT / filename,
        APP_ROOT / "models" / filename,
        PROJECT_ROOT / "models" / filename,
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]

export class PredictionOverlayView {
  constructor(overlay) {
    this.overlay = overlay;
  }

  setState(state, text) {
    this.overlay.className = "overlay";
    this.overlay.classList.add(`overlay-${state}`);
    this.overlay.textContent = text;
  }

  showIdle() {
    this.setState("idle", "No hand");
  }

  showNoHand() {
    this.setState("no-hand", "No hand");
  }

  showUnsure() {
    this.setState("unsure", "Unsure");
  }

  showPrediction(label, confidence) {
    this.setState("predicted", `${label} ${confidence.toFixed(1)}%`);
  }

  showLoading(modelKey) {
    this.setState("loading", `Loading ${modelKey}...`);
  }
}

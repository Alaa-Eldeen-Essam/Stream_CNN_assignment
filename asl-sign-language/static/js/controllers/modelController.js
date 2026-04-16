export class ModelController {
  constructor({ state, controlsView, statusView, overlayView, landmarkOverlayView, debugPanelView }) {
    this.state = state;
    this.controlsView = controlsView;
    this.statusView = statusView;
    this.overlayView = overlayView;
    this.landmarkOverlayView = landmarkOverlayView;
    this.debugPanelView = debugPanelView;
  }

  bindEvents() {
    this.controlsView.onModelChange((modelKey) => this.startModelSwitch(modelKey));
  }

  setInitialModel(modelKey) {
    this.controlsView.selectedModel = modelKey;
  }

  startModelSwitch(modelKey) {
    this.state.startModelSwitch(modelKey);
    this.landmarkOverlayView.clear();
    this.controlsView.setSwitching(true);
    this.overlayView.showLoading(modelKey);
    this.statusView.setServerStatus(`Loading model: ${modelKey}...`);
    this.debugPanelView.hideMaskedPreview();
  }

  updateFromPrediction(prediction) {
    if (!this.state.pendingModelSwitch) {
      return;
    }

    if (prediction.model === this.state.pendingModelSwitch) {
      this.statusView.setServerStatus(`Model ready: ${prediction.model}`);
      this.state.finishModelSwitch();
      this.controlsView.setSwitching(false);
    } else {
      this.statusView.setServerStatus(`Requested ${this.state.pendingModelSwitch}, serving ${prediction.model}`);
    }
  }
}

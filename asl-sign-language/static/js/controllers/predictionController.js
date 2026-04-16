import { normalizePrediction } from "../models/predictionModel.js";

export class PredictionController {
  constructor({ state, statusView, overlayView, landmarkOverlayView, debugPanelView, modelController }) {
    this.state = state;
    this.statusView = statusView;
    this.overlayView = overlayView;
    this.landmarkOverlayView = landmarkOverlayView;
    this.debugPanelView = debugPanelView;
    this.modelController = modelController;
  }

  handlePrediction(rawPrediction) {
    const prediction = normalizePrediction(rawPrediction);
    this.state.setFrameInFlight(false);

    this.landmarkOverlayView.draw(prediction.landmarks, prediction.connections, prediction.bbox);
    this.debugPanelView.renderScores(prediction);
    this.debugPanelView.renderMaskedPreview(prediction);
    this.modelController.updateFromPrediction(prediction);
    this.renderOverlay(prediction);

    const fps = this.state.tickFps();
    if (fps !== null) {
      this.statusView.setFps(fps);
    }
  }

  renderOverlay(prediction) {
    if (prediction.state === "predicted") {
      this.overlayView.showPrediction(prediction.label, prediction.confidence);
      return;
    }

    if (prediction.state === "unsure") {
      this.overlayView.showUnsure();
      return;
    }

    this.overlayView.showNoHand();
    this.landmarkOverlayView.clear();
  }
}

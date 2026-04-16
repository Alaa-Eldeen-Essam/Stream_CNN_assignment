export class AppController {
  constructor({
    state,
    socketService,
    frameCaptureService,
    cameraController,
    modelController,
    predictionController,
    controlsView,
    statusView,
    overlayView,
    landmarkOverlayView,
    debugPanelView,
    frameIntervalMs,
  }) {
    this.state = state;
    this.socketService = socketService;
    this.frameCaptureService = frameCaptureService;
    this.cameraController = cameraController;
    this.modelController = modelController;
    this.predictionController = predictionController;
    this.controlsView = controlsView;
    this.statusView = statusView;
    this.overlayView = overlayView;
    this.landmarkOverlayView = landmarkOverlayView;
    this.debugPanelView = debugPanelView;
    this.frameIntervalMs = frameIntervalMs;
  }

  start(defaultModel) {
    this.bindSocketEvents();
    this.bindBrowserEvents();
    this.cameraController.bindEvents();
    this.modelController.bindEvents();

    this.modelController.setInitialModel(defaultModel);
    this.controlsView.setSwitching(false);
    this.overlayView.showIdle();
    this.debugPanelView.reset();
    this.cameraController.startCamera();
    this.state.frameTimerId = window.setInterval(() => this.captureAndSend(), this.frameIntervalMs);
  }

  bindSocketEvents() {
    this.socketService.onConnect(() => {
      this.state.setFrameInFlight(false);
      this.statusView.setServerStatus("Connected to server");
    });

    this.socketService.onDisconnect(() => {
      this.state.resetConnectionState();
      this.controlsView.setSwitching(false);
      this.statusView.setServerStatus("Disconnected");
      this.debugPanelView.reset("Disconnected from server.");
    });

    this.socketService.onPrediction((data) => this.predictionController.handlePrediction(data));
  }

  bindBrowserEvents() {
    window.addEventListener("resize", () => this.landmarkOverlayView.resize());
    window.addEventListener("beforeunload", () => this.stop());
    this.landmarkOverlayView.video.addEventListener("loadedmetadata", () => this.landmarkOverlayView.resize());
    this.debugPanelView.onMaskedPreviewToggle((isEnabled) => {
      if (!isEnabled) {
        this.debugPanelView.hideMaskedPreview();
      }
    });
  }

  captureAndSend() {
    if (!this.socketService.connected || !this.frameCaptureService.isReady() || this.state.frameInFlight) {
      return;
    }

    const frame = this.frameCaptureService.captureBase64();
    this.state.setFrameInFlight(true);
    this.socketService.sendVideoFrame({
      frame,
      model: this.controlsView.selectedModel,
    });
  }

  stop() {
    if (this.state.frameTimerId) {
      window.clearInterval(this.state.frameTimerId);
      this.state.frameTimerId = null;
    }
    this.cameraController.stopCamera();
    this.socketService.disconnect();
  }
}

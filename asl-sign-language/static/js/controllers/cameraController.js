import { describeCameraError } from "../utils/cameraErrors.js";

export class CameraController {
  constructor({ state, cameraService, controlsView, statusView, overlayView, landmarkOverlayView, debugPanelView }) {
    this.state = state;
    this.cameraService = cameraService;
    this.controlsView = controlsView;
    this.statusView = statusView;
    this.overlayView = overlayView;
    this.landmarkOverlayView = landmarkOverlayView;
    this.debugPanelView = debugPanelView;
  }

  bindEvents() {
    this.controlsView.onCameraChange((deviceId) => this.startCamera(deviceId));
    this.controlsView.onRetryCamera((deviceId) => this.startCamera(deviceId));
  }

  async startCamera(deviceId = this.controlsView.selectedCameraId) {
    if (!this.cameraService.isSupported()) {
      this.statusView.setCameraStatus("Camera error: getUserMedia is not supported in this browser.");
      return;
    }

    this.stopCamera();
    this.statusView.setCameraStatus("Starting camera...");

    try {
      const stream = await this.cameraService.start(deviceId);
      this.state.setActiveStream(stream);
      this.landmarkOverlayView.resize();
      await this.refreshCameraOptions(stream);
      this.statusView.setCameraStatus("Camera active");
    } catch (err) {
      this.landmarkOverlayView.clear();
      this.overlayView.showNoHand();
      this.statusView.setCameraStatus(`Camera error: ${describeCameraError(err)}`);
      this.debugPanelView.reset("Camera not ready.");
    }
  }

  stopCamera() {
    this.cameraService.stop(this.state.activeStream);
    this.state.clearActiveStream();
  }

  async refreshCameraOptions(stream) {
    const cameras = await this.cameraService.enumerateCameras();
    const [track] = stream.getVideoTracks();
    const settings = track?.getSettings?.() || {};
    this.controlsView.populateCameraOptions(cameras, settings.deviceId || "");
  }
}

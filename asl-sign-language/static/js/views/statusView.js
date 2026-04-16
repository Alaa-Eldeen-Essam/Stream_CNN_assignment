export class StatusView {
  constructor({ status, cameraStatus, fpsCounter }) {
    this.status = status;
    this.cameraStatus = cameraStatus;
    this.fpsCounter = fpsCounter;
  }

  setServerStatus(message) {
    this.status.textContent = message;
  }

  setCameraStatus(message) {
    this.cameraStatus.textContent = message;
  }

  setFps(fps) {
    this.fpsCounter.textContent = `${fps} fps`;
  }
}

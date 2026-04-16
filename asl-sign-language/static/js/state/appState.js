export class AppState {
  constructor() {
    this.fpsCount = 0;
    this.lastFpsTick = Date.now();
    this.activeStream = null;
    this.frameInFlight = false;
    this.pendingModelSwitch = null;
    this.frameTimerId = null;
  }

  setActiveStream(stream) {
    this.activeStream = stream;
  }

  clearActiveStream() {
    this.activeStream = null;
  }

  setFrameInFlight(value) {
    this.frameInFlight = value;
  }

  startModelSwitch(modelKey) {
    this.pendingModelSwitch = modelKey;
    this.frameInFlight = false;
  }

  finishModelSwitch() {
    this.pendingModelSwitch = null;
  }

  resetConnectionState() {
    this.frameInFlight = false;
    this.pendingModelSwitch = null;
  }

  tickFps() {
    this.fpsCount += 1;
    const now = Date.now();
    if (now - this.lastFpsTick < 1000) {
      return null;
    }

    const fps = this.fpsCount;
    this.fpsCount = 0;
    this.lastFpsTick = now;
    return fps;
  }
}

export class CameraService {
  constructor(videoElement) {
    this.video = videoElement;
  }

  isSupported() {
    return Boolean(navigator.mediaDevices?.getUserMedia);
  }

  canEnumerateDevices() {
    return Boolean(navigator.mediaDevices?.enumerateDevices);
  }

  async enumerateCameras() {
    if (!this.canEnumerateDevices()) {
      return [];
    }

    const devices = await navigator.mediaDevices.enumerateDevices();
    return devices.filter((device) => device.kind === "videoinput");
  }

  async start(deviceId = "") {
    const requestedVideo = deviceId
      ? { deviceId: { exact: deviceId } }
      : { facingMode: "user", width: { ideal: 960 }, height: { ideal: 720 } };

    const attempts = [
      { video: requestedVideo, audio: false },
      { video: deviceId ? { deviceId: { exact: deviceId } } : true, audio: false },
    ];

    let lastError = null;
    for (const constraints of attempts) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        this.video.srcObject = stream;
        await this.video.play();
        return stream;
      } catch (err) {
        lastError = err;
      }
    }

    throw lastError;
  }

  stop(stream) {
    if (!stream) {
      return;
    }

    stream.getTracks().forEach((track) => track.stop());
    this.video.srcObject = null;
  }
}

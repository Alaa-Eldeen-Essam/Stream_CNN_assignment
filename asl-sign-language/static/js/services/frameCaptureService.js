export class FrameCaptureService {
  constructor(video, canvas, context, jpegQuality) {
    this.video = video;
    this.canvas = canvas;
    this.context = context;
    this.jpegQuality = jpegQuality;
  }

  isReady() {
    return Boolean(this.video.videoWidth && this.video.videoHeight);
  }

  captureBase64() {
    this.canvas.width = this.video.videoWidth;
    this.canvas.height = this.video.videoHeight;
    this.context.drawImage(this.video, 0, 0);
    return this.canvas.toDataURL("image/jpeg", this.jpegQuality);
  }
}

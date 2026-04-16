export class LandmarkOverlayView {
  constructor(canvas, context, video) {
    this.canvas = canvas;
    this.context = context;
    this.video = video;
  }

  resize() {
    if (!this.video.videoWidth || !this.video.videoHeight) {
      return;
    }

    this.canvas.width = this.video.videoWidth;
    this.canvas.height = this.video.videoHeight;
  }

  clear() {
    this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  draw(landmarks, connections, bbox) {
    this.clear();
    if (!landmarks.length) {
      return;
    }

    const width = this.canvas.width;
    const height = this.canvas.height;

    this.context.save();
    this.context.lineWidth = 3;
    this.context.strokeStyle = "rgba(96, 165, 250, 0.95)";

    connections.forEach(([startIdx, endIdx]) => {
      const start = landmarks[startIdx];
      const end = landmarks[endIdx];
      if (!start || !end) {
        return;
      }

      this.context.beginPath();
      this.context.moveTo(start.x * width, start.y * height);
      this.context.lineTo(end.x * width, end.y * height);
      this.context.stroke();
    });

    landmarks.forEach((point) => {
      this.context.beginPath();
      this.context.fillStyle = "rgba(34, 211, 238, 0.98)";
      this.context.arc(point.x * width, point.y * height, 5, 0, Math.PI * 2);
      this.context.fill();
    });

    this.drawBBox(bbox);
    this.context.restore();
  }

  drawBBox(bbox) {
    if (!bbox) {
      return;
    }

    const width = this.canvas.width;
    const height = this.canvas.height;

    this.context.save();
    this.context.strokeStyle = "rgba(96, 165, 250, 0.9)";
    this.context.lineWidth = 3;
    this.context.strokeRect(
      bbox.x1 * width,
      bbox.y1 * height,
      (bbox.x2 - bbox.x1) * width,
      (bbox.y2 - bbox.y1) * height,
    );
    this.context.restore();
  }
}

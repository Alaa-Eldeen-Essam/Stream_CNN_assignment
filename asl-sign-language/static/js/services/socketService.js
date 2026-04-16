export class SocketService {
  constructor({ transports }) {
    this.socket = io({ transports });
  }

  get connected() {
    return this.socket.connected;
  }

  onConnect(handler) {
    this.socket.on("connect", handler);
  }

  onDisconnect(handler) {
    this.socket.on("disconnect", handler);
  }

  onPrediction(handler) {
    this.socket.on("prediction", handler);
  }

  sendVideoFrame(payload) {
    this.socket.emit("video_frame", payload);
  }

  disconnect() {
    this.socket.disconnect();
  }
}

import { APP_CONFIG } from "./config.js";
import { AppController } from "./controllers/appController.js";
import { CameraController } from "./controllers/cameraController.js";
import { ModelController } from "./controllers/modelController.js";
import { PredictionController } from "./controllers/predictionController.js";
import { AppState } from "./state/appState.js";
import { CameraService } from "./services/cameraService.js";
import { FrameCaptureService } from "./services/frameCaptureService.js";
import { SocketService } from "./services/socketService.js";
import { ControlsView } from "./views/controlsView.js";
import { DebugPanelView } from "./views/debugPanelView.js";
import { LandmarkOverlayView } from "./views/landmarkOverlayView.js";
import { PredictionOverlayView } from "./views/predictionOverlayView.js";
import { StatusView } from "./views/statusView.js";
import { createAppElements } from "./utils/dom.js";

const elements = createAppElements();
const state = new AppState();

const statusView = new StatusView(elements);
const controlsView = new ControlsView(elements);
const landmarkOverlayView = new LandmarkOverlayView(
  elements.landmarkCanvas,
  elements.landmarkCtx,
  elements.video,
);
const debugPanelView = new DebugPanelView(elements);
const overlayView = new PredictionOverlayView(elements.overlay);

const socketService = new SocketService({ transports: APP_CONFIG.socketTransports });
const cameraService = new CameraService(elements.video);
const frameCaptureService = new FrameCaptureService(
  elements.video,
  elements.captureCanvas,
  elements.captureCtx,
  APP_CONFIG.jpegQuality,
);

const cameraController = new CameraController({
  state,
  cameraService,
  controlsView,
  statusView,
  overlayView,
  landmarkOverlayView,
  debugPanelView,
});

const modelController = new ModelController({
  state,
  controlsView,
  statusView,
  overlayView,
  landmarkOverlayView,
  debugPanelView,
});

const predictionController = new PredictionController({
  state,
  statusView,
  overlayView,
  landmarkOverlayView,
  debugPanelView,
  modelController,
});

const appController = new AppController({
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
  frameIntervalMs: APP_CONFIG.frameIntervalMs,
});

appController.start(APP_CONFIG.defaultModel);

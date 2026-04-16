function getRequiredElement(id) {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`Missing required element: #${id}`);
  }
  return element;
}

function getCanvasContext(canvas, label) {
  const context = canvas.getContext("2d");
  if (!context) {
    throw new Error(`Could not create 2D context for ${label}`);
  }
  return context;
}

export function createAppElements() {
  const captureCanvas = getRequiredElement("captureCanvas");
  const landmarkCanvas = getRequiredElement("landmarkCanvas");

  return {
    video: getRequiredElement("video"),
    captureCanvas,
    captureCtx: getCanvasContext(captureCanvas, "captureCanvas"),
    landmarkCanvas,
    landmarkCtx: getCanvasContext(landmarkCanvas, "landmarkCanvas"),
    overlay: getRequiredElement("overlay"),
    status: getRequiredElement("status"),
    cameraStatus: getRequiredElement("camera-status"),
    fpsCounter: getRequiredElement("fps-counter"),
    modelSelect: getRequiredElement("modelSelect"),
    cameraSelect: getRequiredElement("cameraSelect"),
    retryCamera: getRequiredElement("retryCamera"),
    debugReason: getRequiredElement("debugReason"),
    debugScores: getRequiredElement("debugScores"),
    showMaskedToggle: getRequiredElement("showMaskedToggle"),
    maskedPreviewWrap: getRequiredElement("maskedPreviewWrap"),
    maskedPreview: getRequiredElement("maskedPreview"),
  };
}

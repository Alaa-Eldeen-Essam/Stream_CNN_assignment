const socket = io({ transports: ["polling"] });
const video = document.getElementById("video");
const captureCanvas = document.getElementById("captureCanvas");
const captureCtx = captureCanvas.getContext("2d");
const landmarkCanvas = document.getElementById("landmarkCanvas");
const landmarkCtx = landmarkCanvas.getContext("2d");
const overlay = document.getElementById("overlay");
const status = document.getElementById("status");
const cameraStatus = document.getElementById("camera-status");
const fpsEl = document.getElementById("fps-counter");
const modelSel = document.getElementById("modelSelect");
const cameraSel = document.getElementById("cameraSelect");
const retryBtn = document.getElementById("retryCamera");

let fpsCount = 0;
let lastFpsTick = Date.now();
let activeStream = null;
let frameInFlight = false;
let pendingModelSwitch = null;

function setCameraStatus(message) {
  cameraStatus.textContent = message;
}

function setOverlayState(state, text) {
  overlay.className = "overlay";
  overlay.classList.add(`overlay-${state}`);
  overlay.textContent = text;
}

function setModelSwitchingState(isSwitching) {
  modelSel.disabled = isSwitching;
  cameraSel.disabled = isSwitching;
  retryBtn.disabled = isSwitching;
}

function describeCameraError(err) {
  const errorMap = {
    NotAllowedError: "Camera permission was denied.",
    NotFoundError: "No camera was found on this device.",
    NotReadableError: "The camera is busy or blocked by another app or tab.",
    OverconstrainedError: "The selected camera does not support the requested settings.",
    SecurityError: "Camera access is blocked because the page is not trusted.",
    AbortError: "The browser aborted camera startup.",
  };
  const prefix = errorMap[err.name] || "Camera failed to start.";
  return `${prefix} (${err.name}: ${err.message})`;
}

function resizeOverlayCanvas() {
  if (!video.videoWidth || !video.videoHeight) return;
  landmarkCanvas.width = video.videoWidth;
  landmarkCanvas.height = video.videoHeight;
}

function clearOverlayDrawing() {
  landmarkCtx.clearRect(0, 0, landmarkCanvas.width, landmarkCanvas.height);
}

function drawBBox(bbox) {
  if (!bbox) return;
  const width = landmarkCanvas.width;
  const height = landmarkCanvas.height;

  landmarkCtx.save();
  landmarkCtx.strokeStyle = "rgba(96, 165, 250, 0.9)";
  landmarkCtx.lineWidth = 3;
  landmarkCtx.strokeRect(
    bbox.x1 * width,
    bbox.y1 * height,
    (bbox.x2 - bbox.x1) * width,
    (bbox.y2 - bbox.y1) * height,
  );
  landmarkCtx.restore();
}

function drawLandmarks(landmarks, connections, bbox) {
  clearOverlayDrawing();
  if (!landmarks?.length) return;

  const width = landmarkCanvas.width;
  const height = landmarkCanvas.height;

  landmarkCtx.save();
  landmarkCtx.lineWidth = 3;
  landmarkCtx.strokeStyle = "rgba(96, 165, 250, 0.95)";
  connections.forEach(([startIdx, endIdx]) => {
    const start = landmarks[startIdx];
    const end = landmarks[endIdx];
    if (!start || !end) return;
    landmarkCtx.beginPath();
    landmarkCtx.moveTo(start.x * width, start.y * height);
    landmarkCtx.lineTo(end.x * width, end.y * height);
    landmarkCtx.stroke();
  });

  landmarks.forEach((point) => {
    landmarkCtx.beginPath();
    landmarkCtx.fillStyle = "rgba(34, 211, 238, 0.98)";
    landmarkCtx.arc(point.x * width, point.y * height, 5, 0, Math.PI * 2);
    landmarkCtx.fill();
  });

  drawBBox(bbox);
  landmarkCtx.restore();
}

function stopActiveStream() {
  if (!activeStream) return;
  activeStream.getTracks().forEach((track) => track.stop());
  activeStream = null;
  video.srcObject = null;
}

async function populateCameraOptions() {
  if (!navigator.mediaDevices?.enumerateDevices) return;

  const devices = await navigator.mediaDevices.enumerateDevices();
  const cameras = devices.filter((device) => device.kind === "videoinput");
  const previousValue = cameraSel.value;

  cameraSel.innerHTML = '<option value="">Default camera</option>';
  cameras.forEach((camera, index) => {
    const option = document.createElement("option");
    option.value = camera.deviceId;
    option.textContent = camera.label || `Camera ${index + 1}`;
    cameraSel.appendChild(option);
  });

  if ([...cameraSel.options].some((option) => option.value === previousValue)) {
    cameraSel.value = previousValue;
  }
}

async function startCamera(deviceId = cameraSel.value) {
  if (!navigator.mediaDevices?.getUserMedia) {
    setCameraStatus("Camera error: getUserMedia is not supported in this browser.");
    return;
  }

  stopActiveStream();
  setCameraStatus("Starting camera...");

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
      activeStream = stream;
      video.srcObject = stream;
      await video.play();
      resizeOverlayCanvas();
      await populateCameraOptions();

      const [track] = stream.getVideoTracks();
      const settings = track?.getSettings?.() || {};
      if (settings.deviceId && [...cameraSel.options].some((option) => option.value === settings.deviceId)) {
        cameraSel.value = settings.deviceId;
      }

      setCameraStatus("Camera active ✓");
      return;
    } catch (err) {
      lastError = err;
    }
  }

  clearOverlayDrawing();
  setOverlayState("no-hand", "No hand");
  setCameraStatus(`Camera error: ${describeCameraError(lastError)}`);
}

socket.on("connect", () => {
  frameInFlight = false;
  status.textContent = "Connected to server ✓";
});

socket.on("disconnect", () => {
  frameInFlight = false;
  pendingModelSwitch = null;
  setModelSwitchingState(false);
  status.textContent = "Disconnected";
});

socket.on("prediction", (data) => {
  frameInFlight = false;
  drawLandmarks(data.landmarks, data.connections, data.bbox);

  if (pendingModelSwitch) {
    if (data.model === pendingModelSwitch) {
      status.textContent = `Model ready: ${data.model} ✓`;
      pendingModelSwitch = null;
      setModelSwitchingState(false);
    } else {
      status.textContent = `Requested ${pendingModelSwitch}, serving ${data.model}`;
    }
  }

  if (data.state === "predicted") {
    setOverlayState("predicted", `${data.label} ${data.confidence.toFixed(1)}%`);
  } else if (data.state === "unsure") {
    setOverlayState("unsure", "Unsure");
  } else {
    setOverlayState("no-hand", "No hand");
    clearOverlayDrawing();
  }

  fpsCount += 1;
  const now = Date.now();
  if (now - lastFpsTick >= 1000) {
    fpsEl.textContent = `${fpsCount} fps`;
    fpsCount = 0;
    lastFpsTick = now;
  }
});

function captureAndSend() {
  if (!socket.connected || !video.videoWidth || frameInFlight) return;

  captureCanvas.width = video.videoWidth;
  captureCanvas.height = video.videoHeight;
  captureCtx.drawImage(video, 0, 0);
  const b64 = captureCanvas.toDataURL("image/jpeg", 0.7);
  frameInFlight = true;
  socket.emit("video_frame", { frame: b64, model: modelSel.value });
}

video.addEventListener("loadedmetadata", resizeOverlayCanvas);
window.addEventListener("resize", resizeOverlayCanvas);
modelSel.addEventListener("change", () => {
  pendingModelSwitch = modelSel.value;
  frameInFlight = false;
  clearOverlayDrawing();
  setModelSwitchingState(true);
  setOverlayState("loading", `Loading ${pendingModelSwitch}...`);
  status.textContent = `Loading model: ${pendingModelSwitch}...`;
});
cameraSel.addEventListener("change", () => {
  startCamera(cameraSel.value);
});
retryBtn.addEventListener("click", () => {
  startCamera(cameraSel.value);
});

setInterval(captureAndSend, 200);
modelSel.value = window.APP_CONFIG.defaultModel || modelSel.value;
setModelSwitchingState(false);
setOverlayState("idle", "No hand");
startCamera();

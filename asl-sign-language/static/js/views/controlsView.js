export class ControlsView {
  constructor({ modelSelect, cameraSelect, retryCamera }) {
    this.modelSelect = modelSelect;
    this.cameraSelect = cameraSelect;
    this.retryCamera = retryCamera;
  }

  get selectedModel() {
    return this.modelSelect.value;
  }

  set selectedModel(modelKey) {
    if (modelKey) {
      this.modelSelect.value = modelKey;
    }
  }

  get selectedCameraId() {
    return this.cameraSelect.value;
  }

  setSwitching(isSwitching) {
    this.modelSelect.disabled = isSwitching;
    this.cameraSelect.disabled = isSwitching;
    this.retryCamera.disabled = isSwitching;
  }

  populateCameraOptions(cameras, selectedDeviceId = "") {
    const previousValue = selectedDeviceId || this.cameraSelect.value;
    this.cameraSelect.innerHTML = '<option value="">Default camera</option>';

    cameras.forEach((camera, index) => {
      const option = document.createElement("option");
      option.value = camera.deviceId;
      option.textContent = camera.label || `Camera ${index + 1}`;
      this.cameraSelect.appendChild(option);
    });

    if ([...this.cameraSelect.options].some((option) => option.value === previousValue)) {
      this.cameraSelect.value = previousValue;
    }
  }

  onModelChange(handler) {
    this.modelSelect.addEventListener("change", () => handler(this.selectedModel));
  }

  onCameraChange(handler) {
    this.cameraSelect.addEventListener("change", () => handler(this.selectedCameraId));
  }

  onRetryCamera(handler) {
    this.retryCamera.addEventListener("click", () => handler(this.selectedCameraId));
  }
}

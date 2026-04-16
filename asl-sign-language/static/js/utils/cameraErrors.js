export function describeCameraError(err) {
  const errorMap = {
    NotAllowedError: "Camera permission was denied.",
    NotFoundError: "No camera was found on this device.",
    NotReadableError: "The camera is busy or blocked by another app or tab.",
    OverconstrainedError: "The selected camera does not support the requested settings.",
    SecurityError: "Camera access is blocked because the page is not trusted.",
    AbortError: "The browser aborted camera startup.",
  };
  const prefix = errorMap[err?.name] || "Camera failed to start.";
  return `${prefix} (${err?.name || "UnknownError"}: ${err?.message || "No details"})`;
}

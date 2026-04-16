const VALID_STATES = new Set(["no_hand", "unsure", "predicted"]);

function normalizeTopScores(scores) {
  if (!Array.isArray(scores)) {
    return [];
  }

  return scores.map((item) => ({
    label: String(item?.label || "?"),
    confidence: Number.isFinite(Number(item?.confidence)) ? Number(item.confidence) : 0,
  }));
}

function normalizeLandmarks(landmarks) {
  if (!Array.isArray(landmarks)) {
    return [];
  }

  return landmarks
    .map((point) => ({
      x: Number(point?.x),
      y: Number(point?.y),
    }))
    .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));
}

function normalizeConnections(connections) {
  if (!Array.isArray(connections)) {
    return [];
  }

  return connections.filter(
    (edge) =>
      Array.isArray(edge) &&
      edge.length === 2 &&
      Number.isInteger(Number(edge[0])) &&
      Number.isInteger(Number(edge[1])),
  );
}

function normalizeBbox(bbox) {
  if (!bbox || typeof bbox !== "object") {
    return null;
  }

  const normalized = {
    x1: Number(bbox.x1),
    y1: Number(bbox.y1),
    x2: Number(bbox.x2),
    y2: Number(bbox.y2),
  };

  return Object.values(normalized).every(Number.isFinite) ? normalized : null;
}

export function normalizePrediction(raw) {
  const state = VALID_STATES.has(raw?.state) ? raw.state : "no_hand";

  return {
    state,
    label: String(raw?.label || ""),
    confidence: Number.isFinite(Number(raw?.confidence)) ? Number(raw.confidence) : 0,
    model: String(raw?.model || ""),
    handDetected: Boolean(raw?.hand_detected),
    landmarks: normalizeLandmarks(raw?.landmarks),
    connections: normalizeConnections(raw?.connections),
    bbox: normalizeBbox(raw?.bbox),
    topScores: normalizeTopScores(raw?.top_scores),
    rejectionReason: String(raw?.rejection_reason || ""),
    maskedPreview: String(raw?.masked_preview || ""),
  };
}

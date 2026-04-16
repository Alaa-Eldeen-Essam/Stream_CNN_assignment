export class DebugPanelView {
  constructor({ debugReason, debugScores, showMaskedToggle, maskedPreviewWrap, maskedPreview }) {
    this.debugReason = debugReason;
    this.debugScores = debugScores;
    this.showMaskedToggle = showMaskedToggle;
    this.maskedPreviewWrap = maskedPreviewWrap;
    this.maskedPreview = maskedPreview;
  }

  reset(message = "No inference yet.") {
    this.debugReason.textContent = message;
    this.debugScores.innerHTML = "";
    this.hideMaskedPreview();
  }

  renderScores(prediction) {
    if (!prediction.topScores.length) {
      this.debugReason.textContent = prediction.rejectionReason || "No inference yet.";
      this.debugScores.innerHTML = "";
      return;
    }

    this.debugReason.textContent = prediction.rejectionReason || `Serving ${prediction.model}`;
    this.debugScores.innerHTML = prediction.topScores
      .map(
        (item, index) => `
          <div class="debug-score-row">
            <span class="debug-rank">#${index + 1}</span>
            <span class="debug-label">${item.label}</span>
            <span class="debug-value">${item.confidence.toFixed(1)}%</span>
          </div>
        `,
      )
      .join("");
  }

  renderMaskedPreview(prediction) {
    if (!this.showMaskedToggle.checked || !prediction.maskedPreview) {
      this.hideMaskedPreview();
      return;
    }

    this.maskedPreview.src = prediction.maskedPreview;
    this.maskedPreviewWrap.classList.remove("hidden");
  }

  hideMaskedPreview() {
    this.maskedPreviewWrap.classList.add("hidden");
    this.maskedPreview.removeAttribute("src");
  }

  onMaskedPreviewToggle(handler) {
    this.showMaskedToggle.addEventListener("change", () => handler(this.showMaskedToggle.checked));
  }
}

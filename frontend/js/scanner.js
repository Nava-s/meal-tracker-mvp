import { api } from "./api.js";

let scannerInstance = null;

export function initScanner(onResult) {
  const container = document.getElementById("scanner-view");
  if (!container) return;

  if (typeof Html5Qrcode === "undefined") {
    container.innerHTML = `<p class="error">Barcode scanner library not loaded. Please include html5-qrcode.</p>`;
    return;
  }

  const scanner = new Html5Qrcode("scanner-view");
  scannerInstance = scanner;

  scanner
    .start(
      { facingMode: "environment" },
      {
        fps: 10,
        qrbox: { width: 250, height: 150 },
      },
      (decodedText) => {
        scanner.stop().catch(() => {});
        scannerInstance = null;
        onResult(decodedText);
      },
      () => {}
    )
    .catch((err) => {
      container.innerHTML = `<p class="error">Camera error: ${err}</p>`;
    });
}

export function stopScanner() {
  if (scannerInstance) {
    scannerInstance.stop().catch(() => {});
    scannerInstance = null;
  }
}

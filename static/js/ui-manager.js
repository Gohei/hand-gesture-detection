class UIManager {
  #elements;

  constructor() {
    this.#elements = {
      loading: document.getElementById("loading"),
      cameraPermission: document.getElementById("camera-permission"),
      streamContainer: document.getElementById("stream-container"),
      status: document.getElementById("status"),
    };
  }

  showElement(element) {
    if (element) element.classList.remove("hidden");
  }

  hideElement(element) {
    if (element) element.classList.add("hidden");
  }

  showLoading() {
    this.showElement(this.#elements.loading);
  }

  hideLoading() {
    this.hideElement(this.#elements.loading);
  }

  showCameraPermission() {
    this.showElement(this.#elements.cameraPermission);
  }

  hideCameraPermission() {
    this.hideElement(this.#elements.cameraPermission);
  }

  showStreamContainer() {
    this.showElement(this.#elements.streamContainer);
  }

  hideStreamContainer() {
    this.hideElement(this.#elements.streamContainer);
  }

  updateStatus(message) {
    if (this.#elements.status) {
      this.#elements.status.textContent = message;
    }
    console.log("Status:", message);
  }

  handleError(message, error) {
    const fullMessage = `${message}: ${error.message}`;
    this.updateStatus(fullMessage);
    console.error("Error:", fullMessage, error);
  }
}

export const uiManager = new UIManager();

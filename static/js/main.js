import { CameraStreaming } from "./camera-streaming.js";
import { uiManager } from "./ui-manager.js";

async function initApp() {
  try {
    const cameraStreaming = new CameraStreaming();
    await cameraStreaming.init();
  } catch (error) {
    uiManager.handleError("Failed to initialize the application", error);
  }
}

document.addEventListener("DOMContentLoaded", initApp);

window.addEventListener("error", (event) => {
  uiManager.handleError("An unexpected error occurred", event.error);
});

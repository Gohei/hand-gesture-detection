import { CONSTANTS, CONFIG } from "./config.js";
import { uiManager } from "./ui-manager.js";

export class CameraStreaming {
  #state;

  constructor() {
    // Initialize state with DOM elements and streaming status
    this.#state = {
      elements: {
        video: null,
        resultCanvas: null,
        statusDiv: null,
        loadingDiv: null,
        cameraPermissionDiv: null,
        streamContainer: null,
      },
      isStreaming: false,
      cameraConnected: false,
    };
  }

  async #setupCamera() {
    try {
      uiManager.showLoading();
      uiManager.hideCameraPermission();

      // Request camera access and set up video stream
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      this.#state.elements.video.srcObject = stream;

      // Wait for the video metadata to load
      await new Promise((resolve) => {
        this.#state.elements.video.onloadedmetadata = () => {
          resolve();
        };
      });

      await this.#state.elements.video.play();

      // Set up the result canvas now that video dimensions are known
      this.#setupResultCanvas();

      uiManager.updateStatus("Connected to the camera.");
      uiManager.hideLoading();
      uiManager.showStreamContainer();
      this.#state.cameraConnected = true;
    } catch (error) {
      // Handle camera access denial
      uiManager.hideLoading();
      uiManager.showCameraPermission();
      uiManager.updateStatus(
        "Camera access is denied. Please change your browser settings."
      );
      console.error("Failed to connect to the camera:", error);
      this.#state.cameraConnected = false;
      throw error;
    }
  }

  #setupResultCanvas() {
    // Set canvas dimensions to match video feed
    this.#state.elements.resultCanvas.width =
      this.#state.elements.video.videoWidth;
    this.#state.elements.resultCanvas.height =
      this.#state.elements.video.videoHeight;
    console.log(
      `Canvas size set to ${this.#state.elements.resultCanvas.width}x${
        this.#state.elements.resultCanvas.height
      }`
    );
  }

  #createCanvasFromVideo(videoElement) {
    if (
      !videoElement ||
      videoElement.videoWidth === 0 ||
      videoElement.videoHeight === 0
    ) {
      throw new Error("Video element is not ready or has no dimensions.");
    }

    // Create a canvas from the current video frame
    const canvas = document.createElement("canvas");
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    canvas.getContext("2d").drawImage(videoElement, 0, 0);
    return canvas;
  }

  #createBlobFromCanvas(canvas, format) {
    // Convert canvas to blob for sending to server
    return new Promise((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (blob) {
          resolve(blob);
        } else {
          reject(new Error("Failed to create Blob from canvas."));
        }
      }, format);
    });
  }

  async #sendFrame(blob) {
    // Send frame to server for processing
    const formData = new FormData();
    formData.append("image", blob, CONSTANTS.FILE.IMAGE_NAME);

    const response = await fetch(CONFIG.ENDPOINTS.PROCESS_IMAGE, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  async #captureAndSendFrame() {
    if (!this.#state.cameraConnected) {
      console.log(
        "Skipping frame transmission as the camera is not connected."
      );
      return;
    }

    try {
      // Capture frame, send to server, and handle the result
      const canvas = this.#createCanvasFromVideo(this.#state.elements.video);
      const blob = await this.#createBlobFromCanvas(
        canvas,
        CONFIG.IMAGE.FORMAT
      );
      const result = await this.#sendFrame(blob);
      this.#handleResult(result, canvas);
    } catch (error) {
      uiManager.handleError("Frame transmission error", error);
      throw error;
    }
  }

  #handleResult(result, sourceCanvas) {
    if (result.gesture === "No hand detected") {
      uiManager.updateStatus("No hand detected");
      this.#updateResultCanvas(sourceCanvas);
    } else {
      uiManager.updateStatus(`Detected gesture: ${result.gesture}`);
      this.#drawLandmarks(result.landmarks, sourceCanvas);
    }
  }

  #updateResultCanvas(sourceCanvas) {
    // Update result canvas with the source canvas content
    const ctx = this.#state.elements.resultCanvas.getContext("2d");
    ctx.clearRect(
      0,
      0,
      this.#state.elements.resultCanvas.width,
      this.#state.elements.resultCanvas.height
    );
    ctx.drawImage(sourceCanvas, 0, 0);
  }

  #drawLandmarks(landmarks, sourceCanvas) {
    if (!landmarks) return;

    const ctx = this.#state.elements.resultCanvas.getContext("2d");
    ctx.clearRect(
      0,
      0,
      this.#state.elements.resultCanvas.width,
      this.#state.elements.resultCanvas.height
    );
    ctx.drawImage(sourceCanvas, 0, 0);

    // Define hand joint connections
    const connections = [
      [0, 1], // Thumb
      [1, 2],
      [2, 3],
      [3, 4],
      [0, 5], // Index finger
      [5, 6],
      [6, 7],
      [7, 8],
      [0, 9], // Middle finger
      [9, 10],
      [10, 11],
      [11, 12],
      [0, 13], // Ring finger
      [13, 14],
      [14, 15],
      [15, 16],
      [0, 17], // Pinky
      [17, 18],
      [18, 19],
      [19, 20],
    ];

    // Define colors for each finger
    const fingerColors = {
      thumb: "#FF0000", // Red
      index: "#00FF00", // Green
      middle: "#0000FF", // Blue
      ring: "#FFFF00", // Yellow
      pinky: "#FF00FF", // Magenta
    };

    // Function to determine point color based on index
    const getPointColor = (index) => {
      if (index >= 1 && index <= 4) return fingerColors.thumb;
      if (index >= 5 && index <= 8) return fingerColors.index;
      if (index >= 9 && index <= 12) return fingerColors.middle;
      if (index >= 13 && index <= 16) return fingerColors.ring;
      if (index >= 17 && index <= 20) return fingerColors.pinky;
      return "#FFFFFF"; // White for wrist (index 0)
    };

    const baseSize = 3; // Base size for landmarks

    // Draw hand outline
    ctx.beginPath();
    ctx.moveTo(
      landmarks[0].x * ctx.canvas.width,
      landmarks[0].y * ctx.canvas.height
    );
    [5, 9, 13, 17, 0].forEach((index) => {
      ctx.lineTo(
        landmarks[index].x * ctx.canvas.width,
        landmarks[index].y * ctx.canvas.height
      );
    });
    ctx.strokeStyle = "rgba(255, 255, 255, 0.5)";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw connections between joints
    connections.forEach(([start, end]) => {
      ctx.beginPath();
      ctx.moveTo(
        landmarks[start].x * ctx.canvas.width,
        landmarks[start].y * ctx.canvas.height
      );
      ctx.lineTo(
        landmarks[end].x * ctx.canvas.width,
        landmarks[end].y * ctx.canvas.height
      );
      ctx.strokeStyle = getPointColor(end); // Color line based on end point
      ctx.lineWidth = 2;
      ctx.stroke();
    });

    // Draw landmark points
    landmarks.forEach((point, index) => {
      const x = point.x * ctx.canvas.width;
      const y = point.y * ctx.canvas.height;
      const size = baseSize * (1 - point.z); // Adjust size based on depth

      ctx.beginPath();
      ctx.arc(x, y, size, 0, 2 * Math.PI);
      ctx.fillStyle = getPointColor(index);
      ctx.fill();
    });
  }

  async #startStreaming() {
    if (!this.#state.isStreaming) {
      this.#state.isStreaming = true;
      while (this.#state.isStreaming && this.#state.cameraConnected) {
        await this.#captureAndSendFrame();
        await new Promise((resolve) =>
          setTimeout(resolve, 1000 / CONSTANTS.FPS)
        );
      }
    }
  }

  stopStreaming() {
    this.#state.isStreaming = false;
  }

  async #run() {
    await this.#setupCamera();
    await this.#startStreaming();
  }

  #initializeElements() {
    // Initialize DOM elements
    this.#state.elements.video = document.getElementById("video");
    this.#state.elements.resultCanvas = document.getElementById("result");
    this.#state.elements.statusDiv = document.getElementById("status");
    this.#state.elements.loadingDiv = document.getElementById("loading");
    this.#state.elements.cameraPermissionDiv =
      document.getElementById("camera-permission");
    this.#state.elements.streamContainer =
      document.getElementById("stream-container");

    // Log errors if essential elements are not found
    if (!this.#state.elements.video) console.error("Video element not found");
    if (!this.#state.elements.resultCanvas)
      console.error("Result canvas element not found");
  }

  #validateElements() {
    // Ensure all required elements are present
    return (
      this.#state.elements.video &&
      this.#state.elements.resultCanvas &&
      this.#state.elements.statusDiv
    );
  }

  async init() {
    this.#initializeElements();
    if (!this.#validateElements()) {
      console.error("Required DOM elements not found");
      return;
    }
    try {
      await this.#run();
    } catch (error) {
      uiManager.handleError("Initialization error", error);
    }
  }
}

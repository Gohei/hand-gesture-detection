import { CONSTANTS, CONFIG } from './config.js';
import { uiManager } from './ui-manager.js';

export class CameraStreaming {
    #state;
    #clientId;

    constructor() {
        this.#state = {
            elements: {
                video: null,
                resultImg: null,
                statusDiv: null,
                loadingDiv: null,
                cameraPermissionDiv: null,
                streamContainer: null
            },
            isStreaming: false,
            cameraConnected: false
        };
        this.#clientId = this.#generateClientId();
    }

    #generateClientId() {
        const randomBytes = crypto.getRandomValues(new Uint8Array(8));
        return CONSTANTS.CLIENT_ID.PREFIX +
            btoa(randomBytes).replace(/[+/]/g, '').substring(0, CONSTANTS.CLIENT_ID.LENGTH);
    }

    async #setupCamera() {
        try {
            uiManager.showLoading();
            uiManager.hideCameraPermission();

            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            this.#state.elements.video.srcObject = stream;
            await this.#state.elements.video.play();

            uiManager.updateStatus("Connected to the camera.");
            uiManager.hideLoading();
            uiManager.showStreamContainer();
            this.#state.cameraConnected = true;
        } catch (error) {
            uiManager.hideLoading();
            uiManager.showCameraPermission();
            uiManager.updateStatus("Camera access is denied. Please change your browser settings.");
            console.error("Failed to connect to the camera:", error);
            this.#state.cameraConnected = false;
            throw error;
        }
    }

    #createCanvasFromVideo(videoElement) {
        if (!videoElement || videoElement.videoWidth === 0 || videoElement.videoHeight === 0) {
            throw new Error('Video element is not ready or has no dimensions.');
        }

        const canvas = document.createElement('canvas');
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
        canvas.getContext('2d').drawImage(videoElement, 0, 0);
        return canvas;
    }

    #createBlobFromCanvas(canvas, format) {
        return new Promise((resolve, reject) => {
            canvas.toBlob(blob => {
                if (blob) {
                    resolve(blob);
                } else {
                    reject(new Error('Failed to create Blob from canvas.'));
                }
            }, format);
        });
    }

    async #sendFrame(blob) {
        const formData = new FormData();
        formData.append('image', blob, CONSTANTS.FILE.IMAGE_NAME);

        const response = await fetch(`${CONFIG.ENDPOINTS.PROCESS_IMAGE}/${this.#clientId}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
    }

    async #captureAndSendFrame() {
        if (!this.#state.cameraConnected) {
            console.log("Skipping frame transmission as the camera is not connected.");
            return;
        }

        try {
            const canvas = this.#createCanvasFromVideo(this.#state.elements.video);
            const blob = await this.#createBlobFromCanvas(canvas, CONFIG.IMAGE.FORMAT);
            await this.#sendFrame(blob);
        } catch (error) {
            uiManager.handleError("Frame transmission error", error);
            throw error;
        }
    }

    async #fetchLatestResult() {
        // Fetch the latest prediction result from the server
        console.log('Fetching the latest result for client:', this.#clientId);

        try {
            // Correctly construct the endpoint URL with encoded client ID
            const endpoint = `${CONFIG.ENDPOINTS.LATEST_RESULT}/${encodeURIComponent(this.#clientId)}`;
            console.log('Fetching from endpoint:', endpoint); // Debug log for the constructed URL

            // Fetch request to the server
            const response = await fetch(endpoint, {
                method: 'GET',  // Make sure the method matches what the server expects
                headers: {
                    'Content-Type': 'application/json',  // Ensure headers are correct if needed
                    // Add other headers if necessary
                }
            });

            console.log('Response status:', response.status); // Check response status
            if (!response.ok) {
                // Log detailed error information for debugging
                console.error(`Failed to fetch latest result: ${response.statusText} (${response.status})`);
                throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Received data:', data); // Log the received data for verification

            // Extract and log the prediction from the received data
            const prediction = data.latest_prediction || 'No result yet';
            console.log('Updating status with prediction:', prediction);

            // Update the UI with the latest prediction
            uiManager.updateStatus(`Latest Prediction: ${prediction}`);

        } catch (error) {
            // Log any errors that occurred during the fetch operation
            console.error("Failed to fetch the latest result:", error);
            uiManager.handleError("Failed to fetch the latest result", error);
        }
    }


    async #startStreaming() {
        if (!this.#state.isStreaming) {
            this.#state.isStreaming = true;
            while (this.#state.isStreaming && this.#state.cameraConnected) {
                await this.#captureAndSendFrame();
                await this.#fetchLatestResult(); // Ensure this call happens
                await new Promise(resolve => setTimeout(resolve, 1000 / CONSTANTS.FPS));
            }
        }
    }

    stopStreaming() {
        this.#state.isStreaming = false;
    }

    async #run() {
        await this.#setupCamera();
        this.#state.elements.resultImg.src = `${CONFIG.ENDPOINTS.VIDEO_FEED}/${this.#clientId}`;
        await this.#startStreaming();
    }

    #initializeElements() {
        this.#state.elements.video = document.getElementById('video');
        this.#state.elements.resultImg = document.getElementById('result');
        this.#state.elements.statusDiv = document.getElementById('status');
        this.#state.elements.loadingDiv = document.getElementById('loading');
        this.#state.elements.cameraPermissionDiv = document.getElementById('camera-permission');
        this.#state.elements.streamContainer = document.getElementById('stream-container');
    }

    #validateElements() {
        return this.#state.elements.resultImg && this.#state.elements.statusDiv;
    }

    async init() {
        this.#initializeElements();
        if (!this.#validateElements()) {
            console.error('Required DOM elements not found');
            return;
        }
        try {
            await this.#run();
        } catch (error) {
            uiManager.handleError("Initialization error", error);
        }
    }
}

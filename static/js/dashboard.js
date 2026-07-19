let currentImageName = "";
let latestVoiceText = "";

const imageInput = document.getElementById("imageInput");
const dropZone = document.getElementById("dropZone");
const uploadBtn = document.getElementById("uploadBtn");
const uploadStatus = document.getElementById("uploadStatus");
const processStatus = document.getElementById("processStatus");
const audioStatus = document.getElementById("audioStatus");
const voiceText = document.getElementById("voiceText");
const originalPreview = document.getElementById("originalPreview");
const processedPreview = document.getElementById("processedPreview");
const downloadBtn = document.getElementById("downloadBtn");
const audioInput = document.getElementById("audioInput");
const audioBtn = document.getElementById("audioBtn");
const runVoiceBtn = document.getElementById("runVoiceBtn");
const voiceBtn = document.getElementById("voiceBtn");
const loader = document.getElementById("loader");

function showLoader() { loader.classList.add("show"); }
function hideLoader() { loader.classList.remove("show"); }

function setText(el, text, isError = false) {
    el.textContent = text;
    el.style.color = isError ? "#fecaca" : "#cbd5e1";
}

async function postForm(url, formData) {
    showLoader();
    try {
        const response = await fetch(url, {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "Request failed");
        }
        return data;
    } finally {
        hideLoader();
    }
}

// Drag & Drop Handling
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        imageInput.files = e.dataTransfer.files;
        setText(uploadStatus, "File selected: " + imageInput.files[0].name);
    }
});

imageInput.addEventListener('change', () => {
    if (imageInput.files.length) {
        setText(uploadStatus, "File selected: " + imageInput.files[0].name);
    }
});

// Upload Logic
uploadBtn.addEventListener("click", async () => {
    if (!imageInput.files.length) {
        setText(uploadStatus, "Please choose an image first.", true);
        return;
    }

    const formData = new FormData();
    formData.append("image", imageInput.files[0]);

    setText(uploadStatus, "Uploading image...");
    try {
        const data = await postForm("/upload", formData);
        currentImageName = data.filename;
        originalPreview.src = data.image_url;
        processedPreview.src = "";
        downloadBtn.classList.add("disabled");
        downloadBtn.href = "#";
        setText(uploadStatus, data.message);
        setText(processStatus, "");
    } catch (error) {
        setText(uploadStatus, error.message, true);
    }
});

async function processImage(operation) {
    if (!currentImageName) {
        setText(processStatus, "Upload an image before processing.", true);
        return;
    }

    const formData = new FormData();
    formData.append("image_name", currentImageName);
    formData.append("operation", operation);

    // Simple defaults for operations needing parameters.
    if (operation === "resize") {
        formData.append("width", "500");
        formData.append("height", "500");
    } else if (operation === "rotate") {
        formData.append("angle", "90");
    } else if (operation === "flip") {
        formData.append("mode", "horizontal");
    }

    setText(processStatus, `Applying ${operation}...`);
    try {
        const data = await postForm("/process", formData);
        processedPreview.src = data.processed_url;
        downloadBtn.href = data.download_url;
        downloadBtn.classList.remove("disabled");
        setText(processStatus, `Done: ${data.operation}`);
    } catch (error) {
        setText(processStatus, error.message, true);
    }
}

document.querySelectorAll(".op-btn").forEach((button) => {
    button.addEventListener("click", () => processImage(button.dataset.op));
});

audioBtn.addEventListener("click", async () => {
    if (!currentImageName) {
        setText(audioStatus, "Upload an image first.", true);
        return;
    }
    if (!audioInput.files.length) {
        setText(audioStatus, "Please select a .wav audio file.", true);
        return;
    }

    const formData = new FormData();
    formData.append("audio", audioInput.files[0]);
    formData.append("image_name", currentImageName);

    setText(audioStatus, "Reading audio and applying command...");
    try {
        const data = await postForm("/audio-command", formData);
        processedPreview.src = data.processed_url;
        downloadBtn.href = data.download_url;
        downloadBtn.classList.remove("disabled");
        setText(audioStatus, `Heard: "${data.recognized_text}" -> ${data.operation}`);
    } catch (error) {
        setText(audioStatus, error.message, true);
    }
});

function mapVoiceToOperation(text) {
    const command = text.toLowerCase();
    if (command.includes("grayscale") || command.includes("black and white")) return "grayscale";
    if (command.includes("brightness") || command.includes("brighter")) return "brightness";
    if (command.includes("contrast")) return "contrast";
    if (command.includes("blur")) return "blur";
    if (command.includes("edge")) return "edge";
    if (command.includes("negative") || command.includes("invert")) return "negative";
    if (command.includes("resize")) return "resize";
    if (command.includes("rotate")) return "rotate";
    if (command.includes("flip")) return "flip";
    if (command.includes("noise")) return "noise";
    if (command.includes("face")) return "face";
    return "";
}

runVoiceBtn.addEventListener("click", async () => {
    if (!latestVoiceText) {
        setText(voiceText, "No recognized speech yet.", true);
        return;
    }
    const op = mapVoiceToOperation(latestVoiceText);
    if (!op) {
        setText(voiceText, `Unknown command: "${latestVoiceText}"`, true);
        return;
    }
    await processImage(op);
});

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SpeechRecognition) {
    setText(voiceText, "Speech API not supported.", true);
    voiceBtn.disabled = true;
} else {
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    voiceBtn.addEventListener("click", () => {
        latestVoiceText = "";
        setText(voiceText, "Listening...");
        voiceBtn.classList.add("pulsing");
        recognition.start();
    });

    recognition.onresult = (event) => {
        voiceBtn.classList.remove("pulsing");
        latestVoiceText = event.results[0][0].transcript;
        setText(voiceText, `Recognized: "${latestVoiceText}"`);
    };

    recognition.onerror = () => {
        voiceBtn.classList.remove("pulsing");
        setText(voiceText, "Voice recognition failed. Try again.", true);
    };

    recognition.onend = () => {
        voiceBtn.classList.remove("pulsing");
    };
}

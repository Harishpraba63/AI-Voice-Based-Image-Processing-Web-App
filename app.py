import os
import uuid
from datetime import datetime

import cv2
import speech_recognition as sr
from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret-key")


users = {
    "admin": {
        "password": generate_password_hash("admin123"),
        "is_admin": True,
    }
}

UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
AUDIO_FOLDER = "audio"
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp"}
ALLOWED_AUDIO_EXTENSIONS = {"wav"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)


def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def process_grayscale(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def process_brightness(image, value=40):
    return cv2.convertScaleAbs(image, alpha=1.0, beta=value)


def process_contrast(image, alpha=1.4):
    return cv2.convertScaleAbs(image, alpha=alpha, beta=0)


def process_blur(image, kernel_size=9):
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)


def process_edge_detection(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)


def process_negative(image):
    return cv2.bitwise_not(image)


def process_resize(image, width=500, height=500):
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)


def process_rotate(image, angle=90):
    height, width = image.shape[:2]
    center = (width // 2, height // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, matrix, (width, height))


def process_flip(image, mode="horizontal"):
    flip_code = 1 if mode == "horizontal" else 0
    return cv2.flip(image, flip_code)


def process_noise_removal(image):
    return cv2.medianBlur(image, 5)


def process_face_detection(image):
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    detected = image.copy()
    for (x, y, w, h) in faces:
        cv2.rectangle(detected, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return detected


def command_to_operation(command_text):
    if not command_text:
        return None, {}

    text = command_text.lower().strip()

    command_map = [
        (["grayscale", "gray scale", "make grayscale", "black and white"], "grayscale", {}),
        (["brightness", "increase brightness", "brighter"], "brightness", {"value": 40}),
        (["contrast", "increase contrast"], "contrast", {"alpha": 1.4}),
        (["blur", "blur image", "gaussian blur"], "blur", {"kernel_size": 9}),
        (["edge", "edges", "detect edges", "edge detection"], "edge", {}),
        (["negative", "invert", "invert colors"], "negative", {}),
        (["resize", "resize image"], "resize", {"width": 500, "height": 500}),
        (["rotate", "rotate image"], "rotate", {"angle": 90}),
        (["flip vertical"], "flip", {"mode": "vertical"}),
        (["flip", "flip image", "flip horizontal"], "flip", {"mode": "horizontal"}),
        (["noise", "remove noise", "noise removal"], "noise", {}),
        (["face", "detect face", "face detection"], "face", {}),
    ]

    for phrases, operation, params in command_map:
        if any(phrase in text for phrase in phrases):
            return operation, params
    return None, {}


def run_operation(image, operation, params):
    params = params or {}
    operations = {
        "grayscale": lambda img: process_grayscale(img),
        "brightness": lambda img: process_brightness(img, value=int(params.get("value", 40))),
        "contrast": lambda img: process_contrast(img, alpha=float(params.get("alpha", 1.4))),
        "blur": lambda img: process_blur(img, kernel_size=int(params.get("kernel_size", 9))),
        "edge": lambda img: process_edge_detection(img),
        "negative": lambda img: process_negative(img),
        "resize": lambda img: process_resize(
            img, width=int(params.get("width", 500)), height=int(params.get("height", 500))
        ),
        "rotate": lambda img: process_rotate(img, angle=float(params.get("angle", 90))),
        "flip": lambda img: process_flip(img, mode=params.get("mode", "horizontal")),
        "noise": lambda img: process_noise_removal(img),
        "face": lambda img: process_face_detection(img),
    }
    if operation not in operations:
        return None
    return operations[operation](image)


def save_processed_image(processed_image, original_filename, operation_name):
    name, _ = os.path.splitext(original_filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    processed_filename = f"{name}_{operation_name}_{timestamp}.png"
    processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)
    cv2.imwrite(processed_path, processed_image)
    return processed_filename


def require_login():
    return "username" in session


def require_admin():
    username = session.get("username")
    return username in users and users[username]["is_admin"]


@app.route("/")
def root():
    if "username" in session:
        return redirect(url_for("admin_dashboard" if require_admin() else "dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template("register.html", error="Username and password are required.")
        if username in users:
            return render_template("register.html", error="Username already exists.")

        users[username] = {
            "password": generate_password_hash(password),
            "is_admin": False,
        }
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = users.get(username)
        if not user or not check_password_hash(user["password"], password):
            return render_template("login.html", error="Invalid username or password.")

        session["username"] = username
        return redirect(url_for("admin_dashboard" if user["is_admin"] else "dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if not require_login() or require_admin():
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session["username"])


@app.route("/upload", methods=["POST"])
def upload():
    if not require_login() or require_admin():
        return jsonify({"error": "Unauthorized"}), 401

    if "image" not in request.files:
        return jsonify({"error": "No image file sent"}), 400

    image_file = request.files["image"]
    if image_file.filename == "":
        return jsonify({"error": "No selected image"}), 400
    if not allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
        return jsonify({"error": "Unsupported image type"}), 400

    filename = secure_filename(image_file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    path = os.path.join(UPLOAD_FOLDER, unique_name)
    image_file.save(path)

    session["latest_image"] = unique_name
    return jsonify(
        {
            "message": "Image uploaded successfully",
            "filename": unique_name,
            "image_url": url_for("serve_upload", filename=unique_name),
        }
    )


@app.route("/process", methods=["POST"])
def process():
    if not require_login() or require_admin():
        return jsonify({"error": "Unauthorized"}), 401

    image_name = request.form.get("image_name") or session.get("latest_image")
    operation = request.form.get("operation", "").strip().lower()

    if not image_name:
        return jsonify({"error": "No uploaded image found"}), 400
    if not operation:
        return jsonify({"error": "No operation provided"}), 400

    image_path = os.path.join(UPLOAD_FOLDER, image_name)
    if not os.path.exists(image_path):
        return jsonify({"error": "Image not found"}), 404

    image = cv2.imread(image_path)
    if image is None:
        return jsonify({"error": "Invalid image file"}), 400

    params = {
        "value": request.form.get("value", 40),
        "alpha": request.form.get("alpha", 1.4),
        "kernel_size": request.form.get("kernel_size", 9),
        "width": request.form.get("width", 500),
        "height": request.form.get("height", 500),
        "angle": request.form.get("angle", 90),
        "mode": request.form.get("mode", "horizontal"),
    }
    processed = run_operation(image, operation, params)
    if processed is None:
        return jsonify({"error": "Unsupported operation"}), 400

    processed_name = save_processed_image(processed, image_name, operation)
    return jsonify(
        {
            "message": "Image processed successfully",
            "operation": operation,
            "processed_image": processed_name,
            "processed_url": url_for("serve_processed", filename=processed_name),
            "download_url": url_for("download_processed", filename=processed_name),
        }
    )


@app.route("/audio-command", methods=["POST"])
def audio_command():
    if not require_login() or require_admin():
        return jsonify({"error": "Unauthorized"}), 401

    image_name = request.form.get("image_name") or session.get("latest_image")
    if not image_name:
        return jsonify({"error": "No uploaded image found"}), 400

    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    if audio_file.filename == "":
        return jsonify({"error": "No selected audio"}), 400
    if not allowed_file(audio_file.filename, ALLOWED_AUDIO_EXTENSIONS):
        return jsonify({"error": "Only .wav files are supported"}), 400

    audio_name = secure_filename(audio_file.filename)
    unique_audio = f"{uuid.uuid4().hex}_{audio_name}"
    audio_path = os.path.join(AUDIO_FOLDER, unique_audio)
    audio_file.save(audio_path)

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
        command_text = recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return jsonify({"error": "Could not understand the audio clearly"}), 400
    except sr.RequestError:
        return jsonify({"error": "Speech recognition service unavailable"}), 503
    except Exception as exc:
        return jsonify({"error": f"Audio processing failed: {str(exc)}"}), 500

    operation, params = command_to_operation(command_text)
    if not operation:
        return jsonify({"error": f"No matching command found in: '{command_text}'"}), 400

    image_path = os.path.join(UPLOAD_FOLDER, image_name)
    image = cv2.imread(image_path)
    if image is None:
        return jsonify({"error": "Invalid image file"}), 400

    processed = run_operation(image, operation, params)
    if processed is None:
        return jsonify({"error": "Command mapped to unsupported operation"}), 400

    processed_name = save_processed_image(processed, image_name, operation)
    return jsonify(
        {
            "message": "Audio command processed successfully",
            "recognized_text": command_text,
            "operation": operation,
            "processed_image": processed_name,
            "processed_url": url_for("serve_processed", filename=processed_name),
            "download_url": url_for("download_processed", filename=processed_name),
        }
    )


@app.route("/admin")
def admin_dashboard():
    if not require_login() or not require_admin():
        return redirect(url_for("login"))

    user_list = [name for name in users.keys() if name != "admin"]
    uploaded_images = sorted(os.listdir(UPLOAD_FOLDER))
    processed_images = sorted(os.listdir(PROCESSED_FOLDER))
    return render_template(
        "admin.html",
        username=session["username"],
        users=user_list,
        uploaded_images=uploaded_images,
        processed_images=processed_images,
    )


@app.route("/admin/delete-user/<username>", methods=["POST"])
def delete_user(username):
    if not require_login() or not require_admin():
        return jsonify({"error": "Unauthorized"}), 401
    if username == "admin":
        return jsonify({"error": "Cannot delete admin user"}), 400

    if username in users:
        del users[username]
        return jsonify({"message": f"User '{username}' deleted"})
    return jsonify({"error": "User not found"}), 404


@app.route("/admin/delete-image/<folder>/<filename>", methods=["POST"])
def delete_image(folder, filename):
    if not require_login() or not require_admin():
        return jsonify({"error": "Unauthorized"}), 401

    if folder not in {"uploads", "processed"}:
        return jsonify({"error": "Invalid folder"}), 400

    target_path = os.path.join(folder, secure_filename(filename))
    if os.path.exists(target_path):
        os.remove(target_path)
        return jsonify({"message": "Image deleted"})
    return jsonify({"error": "Image not found"}), 404


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/processed/<path:filename>")
def serve_processed(filename):
    return send_from_directory(PROCESSED_FOLDER, filename)


@app.route("/download/<path:filename>")
def download_processed(filename):
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)

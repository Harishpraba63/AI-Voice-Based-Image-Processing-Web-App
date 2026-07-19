# AI Voice-Based Image Processing Web App

A simple full-stack web project using **Flask + HTML/CSS/JS** with:
- User register/login (in-memory dictionary, no database)
- Admin login and admin dashboard
- Image upload and OpenCV processing
- Live voice command via browser `SpeechRecognition`
- Recorded `.wav` audio command via Python `SpeechRecognition`

## Project Structure

```text
app.py
templates/
static/
uploads/
processed/
audio/
requirements.txt
```

## Features

### User
- Register and login
- Upload an image
- Apply operations:
  - Grayscale
  - Brightness
  - Contrast
  - Gaussian blur
  - Edge detection (Canny)
  - Negative
  - Resize
  - Rotate
  - Flip
  - Noise removal (median blur)
  - Face detection (Haar Cascade)
- Live voice command button
- Audio file command upload (`.wav`)
- Preview original/processed image
- Download processed output

### Admin
- Admin login
- View registered users (in-memory)
- View uploaded and processed files
- Delete users and images

## Default Credentials

- Admin username: `admin`
- Admin password: `admin123`

## Setup and Run

1) Create virtual environment:

```bash
python -m venv .venv
```

2) Activate virtual environment:

- Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

3) Install dependencies:

```bash
pip install -r requirements.txt
```

4) (Optional) Set secret key:

```powershell
$env:FLASK_SECRET_KEY="your-strong-secret"
```

5) Run app:

```bash
python app.py
```

6) Open in browser:

`http://127.0.0.1:5000`

## Notes

- No database is used; users are stored in Python memory and reset when server restarts.
- For live voice recognition, use a browser that supports Web Speech API (Chrome recommended).
- Recorded audio command route accepts `.wav` files.
- If `PyAudio` fails to install on Windows, install wheel tools first:

```bash
pip install pipwin
pipwin install pyaudio
```

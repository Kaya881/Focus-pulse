# AI Study Analyzer

AI Study Analyzer is a Python-based application for monitoring study focus and fatigue using webcam-based face analytics, keyboard/mouse activity tracking, and AI-powered coaching suggestions.

## Key Features

- **Real-time face monitoring** using OpenCV Haar cascades
- **Blink, head direction, and expression detection** to infer student attention
- **Keyboard and mouse activity tracking** on Windows
- **Focus classification**: `FOCUSED`, `DISTRACTED`, `FATIGUED`, or `MONITORING`
- **AI coaching suggestions** powered by a Groq/LLM chat completion API
- **Flask web interface** with account signup/login, dashboard, and live monitoring
- **Standalone camera mode** via `main.py` for direct desktop use

## Repository Contents

- `app.py` - Flask web application entry point
- `main.py` - desktop camera demo for real-time analysis
- `activity.py` - keyboard and mouse listener for activity tracking
- `chatbot.py` - AI suggestion generation and chat helper logic
- `classifier.py` - status classification and face metadata helpers
- `face_detection.py` - face, eye, and smile detection with OpenCV
- `requirements.txt` - Python dependencies
- `templates/` - HTML templates for the Flask app
- `static/` - client-side JavaScript, models, and assets

## Requirements

- Python 3.10+ recommended
- Windows OS (activity tracking uses Windows API)
- Webcam for live face monitoring

## Install

1. Create or activate a virtual environment:

```powershell
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a local environment file from the example:

```powershell
Copy-Item .env.example .env
```

Set `SECRET_KEY` to a unique random value and `GROQ_API_KEY` to your Groq API key in `.env`. Never commit `.env`; it is excluded by `.gitignore`.

## Run the Flask Web App

1. Start the app:

```powershell
python app.py
```

2. Open a browser and visit:

```text
http://127.0.0.1:5000
```

3. Sign up, log in, and access the dashboard for live monitoring.

## Run the Local Camera Mode

Use `main.py` if you want to run the desktop camera demo without the Flask interface:

```powershell
python main.py
```

Press `q` to quit the camera window.

## Notes

- The app stores users in a local SQLite database: `users.db`
- The AI suggestion engine reads `GROQ_API_KEY` from the environment or `.env` and calls the Groq OpenAI-compatible endpoint
- `activity.py` currently uses Windows-specific APIs for keyboard and mouse tracking
- `SECRET_KEY` must be configured locally and should be unique for each deployment

## Troubleshooting

- If the webcam does not open, ensure no other application is using it and that your system permissions allow camera access
- For OpenCV model detection, ensure the correct Haar cascade files are available through the installed OpenCV package
- If Flask fails to start, verify your Python environment and dependencies

## License

This project is provided as-is for educational and prototyping use.

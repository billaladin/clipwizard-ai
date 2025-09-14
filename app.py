import os
import json
import re
import uuid
from flask import Flask, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename

# .env stöd lokalt (ignoreras om paket saknas)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# OpenAI nya SDK
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Video
from moviepy.editor import VideoFileClip

app = Flask(__name__)

# Mappar
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/")
def home():
    return "✅ ClipWizard AI is running!"

@app.route("/health")
def health():
    ok = bool(os.getenv("OPENAI_API_KEY"))
    return jsonify({"ok": True, "openai_key_set": ok})

# ---------------------------
# POST /transcribe
# ---------------------------
@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400

    filename = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
    path = os.path.join(UPLOAD_DIR, filename)
    f.save(path)

    try:
        with open(path, "rb") as audio_file:
            resp = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        text = resp.text
        return jsonify({"filename": filename, "transcription": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------
# POST /generate
# ---------------------------
@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True) or {}
    transcription = data.get("transcription", "").strip()
    max_clips = int(data.get("max_clips", 3))

    if not transcription:
        return jsonify({"error": "No transcription provided"}), 400

    prompt = f"""
Du är en editor som tar en transkription och föreslår upp till {max_clips} highlights
för TikTok/Reels. Varje highlight ska vara 30–60 sek om möjligt.
Svara ENBART som en JSON-array:
[
  {{"start": 12, "end": 41, "name": "clip_1.mp4", "reason": "hook/punchline"}},
  ...
]
Transkription:
{transcription}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You output only JSON arrays with start/end/name/reason."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=400,
        )
        content = resp.choices[0].message.content

        # Försök plocka ut JSON-array
        m = re.search(r'(\[.*\])', content, re.S)
        if not m:
            return jsonify({"raw": content, "warning": "No JSON detected"}), 200

        try:
            clips = json.loads(m.group(1))
        except Exception:
            return jsonify({"raw": content, "warning": "JSON parse failed"}), 200

        # Fallback-namn om saknas
        for i, c in enumerate(clips):
            c.setdefault("name", f"clip_{i+1}.mp4")

        return jsonify({"clips": clips})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------
# POST /clip
# ---------------------------
@app.route("/clip", methods=["POST"])
def clip_video():
    try:
        # Antingen uppladdad fil...
        if "file" in request.files:
            f = request.files["file"]
            filename = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
            in_path = os.path.join(UPLOAD_DIR, filename)
            f.save(in_path)
        else:
            # ...eller referens till tidigare uppladdad fil
            filename = request.form.get("filename", "")
            in_path = os.path.join(UPLOAD_DIR, secure_filename(filename))

        if not os.path.exists(in_path):
            return jsonify({"error": "Input file not found"}), 400

        clips_raw = request.form.get("clips", "")
        if not clips_raw:
            return jsonify({"error": "No clips provided"}), 400

        clips = json.loads(clips_raw)
        out_files = []

        with VideoFileClip(in_path) as base:
            for i, c in enumerate(clips):
                start = float(c.get("start", 0))
                end = float(c.get("end", start + 30))
                name = c.get("name", f"clip_{i+1}.mp4")
                out_path = os.path.join(OUTPUT_DIR, f"{uuid.uuid4().hex}_{secure_filename(name)}")

                sub = base.subclip(start, end)
                # Standard 16:9 output. (Vill du ha 9:16, lägger vi in crop/resize senare.)
                sub.write_videofile(out_path, codec="libx264", audio_codec="aac", threads=2, logger=None)
                out_files.append(os.path.basename(out_path))

        return jsonify({"outputs": out_files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ladda ned genererade klipp
@app.route("/download/<path:fname>")
def download(fname):
    safe = secure_filename(fname)
    full = os.path.join(OUTPUT_DIR, safe)
    if not os.path.exists(full):
        abort(404)
    return send_file(full, as_attachment=True, download_name=safe)

if __name__ == "__main__":
    # Lokalt läge
    app.run(host="0.0.0.0", port=5000)

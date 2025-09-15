import os
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Route for testing
@app.route("/", methods=["GET"])
def home():
    return "Clipwizard AI is running!"

# Route for processing video uploads
@app.route("/process", methods=["POST"])
def process_video():
    if "video" not in request.files:
        return jsonify({"error": "No video uploaded"}), 400

    file = request.files["video"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    output_path = os.path.join(OUTPUT_FOLDER, f"processed_{filename}")

    file.save(input_path)

    try:
        # Example video processing
        clip = VideoFileClip(input_path).subclip(0, 5)
        clip.write_videofile(output_path, codec="libx264")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return send_file(output_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

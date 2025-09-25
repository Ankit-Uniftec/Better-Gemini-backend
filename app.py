import os
import json
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

load_dotenv()
app = Flask(__name__)

# 🌍 Allow CORS for everyone (all origins)
CORS(app, resources={r"/*": {"origins": "*"}})

# Gemini API config
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}'


def generate_gemini_summary(video_url):
    """
    Call Gemini API with a video URL (note: Gemini does not directly support YouTube URLs).
    Ideally, extract transcript/audio first, then send as text/audio.
    """
    headers = {"Content-Type": "application/json"}

    prompt_text = """
You are an expert summarizer.

Tasks:
1. Provide a detailed but concise summary of the video.
2. Provide 5 key takeaways, each with:
   - a heading/title
   - a short explanatory content paragraph

Respond strictly in JSON format as:

{
  "summary": "...",
  "keyTakeaways": [
    {"heading": "...", "content": "..."},
    {"heading": "...", "content": "..."},
    {"heading": "...", "content": "..."},
    {"heading": "...", "content": "..."},
    {"heading": "...", "content": "..."}
  ]
}
"""

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "file_data": {
                            "file_uri": video_url,
                            "mime_type": "video/mp4"
                        }
                    },
                    {
                        "text": prompt_text
                    }
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }

    response = requests.post(GEMINI_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        try:
            json_response = result['candidates'][0]['content']['parts'][0]['text']
            return json.loads(json_response)
        except (KeyError, json.JSONDecodeError, IndexError) as e:
            print("Failed to parse Gemini response:", e)
            print("Raw response:", response.text)
            return None
    else:
        print("Gemini API error:", response.text)
        return None


@app.route('/api/summarize', methods=['POST'])
def summarize():
    try:
        data = request.get_json()

        # Accept both snake_case and camelCase
        video_url = data.get("video_url") or data.get("videoUrl")
        if not video_url:
            return jsonify({"error": "Missing video_url"}), 400

        # 🔹 Call Gemini
        result = generate_gemini_summary(video_url)

        if result:
            return jsonify(result)
        else:
            return jsonify({"error": "Failed to generate summary"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Render uses port from env var
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

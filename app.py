
import os
import re
import json
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_cors import cross_origin

load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Replace with your actual API key (or load from environment)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}'

def generate_gemini_summary(video_url):
    headers = {
        "Content-Type": "application/json"
    }

    # The text prompt is now separate from the video part
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

    # --- THE CRITICAL MODIFICATION STARTS HERE ---
    data = {
        "contents": [
            {
                "parts": [
                    # This part tells Gemini to process the video from the URL
                    {
                        "file_data": {
                            "file_uri": video_url,
                            "mime_type": "video/mp4" # Specify the MIME type for a video
                        }
                    },
                    # This part is your text prompt
                    {
                        "text": prompt_text
                    }
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json" # This is a good practice for JSON mode
        }
    }
    # --- THE CRITICAL MODIFICATION ENDS HERE ---

    response = requests.post(GEMINI_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        try:
            # When you use JSON mode, the response is typically cleaner
            json_response = result['candidates'][0]['content']['parts'][0]['text']
            # We still do a final check to parse the JSON just in case
            return json.loads(json_response)

        except (KeyError, json.JSONDecodeError, IndexError) as e:
            print("Failed to parse Gemini JSON response:", e)
            print("Raw Gemini response:", response.text)
            return None
    else:
        print("Gemini API error:", response.text)
        return None


@app.route('/api/summarize', methods=['POST'])
@cross_origin(origins=["http://localhost:3000", "https://your-frontend-domain.com"])
def summarize():
    try:
        data = request.get_json()
        if not data or "video_url" not in data:
            return jsonify({"error": "Missing video_url"}), 400

        video_url = data["video_url"]

        # 🚨 Dummy response first, test CORS works
        return jsonify({
            "summary": f"Summary for {video_url}",
            "key_takeaways": "Takeaways..."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
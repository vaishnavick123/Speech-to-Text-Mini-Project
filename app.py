from flask import Flask, request, jsonify, render_template  # Import render_template
from flask_cors import CORS
import sqlite3
import wave
import json
from vosk import Model, KaldiRecognizer

app = Flask(__name__)  # This is the only instance of the Flask app you need
CORS(app)

# Load Vosk model (replace this with the path to your downloaded Vosk model)

model = Model("/home/htic_pc_012/code_base/sarvam-ai-test/vosk-model-small-en-us-0.15") 
# model = Model("/home/htic_pc_012/code_base/sarvam-ai-test/vosk-model-small-en-in-0.4")  # Adjust path as necessary

# Homepage route to render the HTML file:
@app.route('/')
def home():
    return render_template('index.html')  # This will render index.html

# Database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Speech-to-Text Endpoint (using Vosk):
@app.route('/stt', methods=['POST'])
def speech_to_text():
    # Check if the file is part of the request
    if 'audio' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    audio_file = request.files['audio']
    
    # If no file is selected
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # Save the uploaded audio file temporarily
        file_path = "/tmp/uploaded_audio.wav"
        audio_file.save(file_path)

        # Open the audio file using the wave library
        wf = wave.open(file_path, "rb")

        # Initialize recognizer
        rec = KaldiRecognizer(model, wf.getframerate())

        # Process audio in chunks and perform speech-to-text
        result = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result += rec.Result()

        # Get the final result from the recognizer
        final_result = rec.FinalResult()

        # Parse the final result (JSON string)
        result_json = json.loads(final_result)

        # Return the transcribed text
        return jsonify({'text': result_json.get('text', '')})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Database Integration
@app.route('/preferences', methods=['POST'])
def save_preferences():
    data = request.json
    user_id = data['user_id']
    preferences = data['preferences']

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO user_preferences (user_id, source_lang, target_lang) VALUES (?, ?, ?)',
        (user_id, preferences['source_lang'], preferences['target_lang'])
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Ensure the app runs correctly

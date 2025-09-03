from flask import Flask, request, send_file
import io
import wave
import struct
import math

app = Flask(__name__)

# Morse code dictionary
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '1': '.----', '2': '..---', '3': '...--',
    '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..',
    '9': '----.', '0': '-----', ' ': '/'
}
REVERSE_DICT = {v: k for k, v in MORSE_CODE_DICT.items()}

# Audio settings
SAMPLE_RATE = 44100
FREQ = 800
DOT = 0.1
DASH = DOT * 3
GAP = DOT

def to_morse(text):
    return ' '.join(MORSE_CODE_DICT.get(c.upper(), '') for c in text)

def from_morse(code):
    return ''.join(REVERSE_DICT.get(c, '') for c in code.split())

def generate_tone(duration):
    samples = int(SAMPLE_RATE * duration)
    return [math.sin(2 * math.pi * FREQ * t / SAMPLE_RATE) for t in range(samples)]

def generate_silence(duration):
    return [0.0] * int(SAMPLE_RATE * duration)

def morse_to_audio(morse):
    audio = []
    for symbol in morse:
        if symbol == '.':
            audio += generate_tone(DOT)
        elif symbol == '-':
            audio += generate_tone(DASH)
        elif symbol == ' ':
            audio += generate_silence(DASH)
        audio += generate_silence(GAP)
    return audio

def save_wav(audio_data):
    buffer = io.BytesIO()
    with wave.open(buffer, 'w') as wav_file:
        wav_file.setparams((1, 2, SAMPLE_RATE, 0, 'NONE', 'not compressed'))
        for sample in audio_data:
            wav_file.writeframes(struct.pack('h', int(sample * 32767)))
    buffer.seek(0)
    return buffer

@app.route('/', methods=['GET', 'POST'])
def index():
    result = ''
    morse = ''
    text = ''
    if request.method == 'POST':
        mode = request.form['mode']
        data = request.form['data']
        if mode == 'encode':
            morse = to_morse(data)
            result = morse
            text = data
        else:
            result = from_morse(data)
            morse = data
            text = result
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Pen Federation Morse Code Translator</title>
    <style>
        body {{
            margin: 0;
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            color: white;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 20px;
        }}
        h1 {{
            font-size: 2.5em;
            animation: wave 2s infinite ease-in-out;
        }}
        @keyframes wave {{
            0% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-10px); }}
            100% {{ transform: translateY(0); }}
        }}
        form {{
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 0 20px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 400px;
        }}
        textarea {{
            width: 100%;
            height: 100px;
            border: none;
            border-radius: 8px;
            padding: 10px;
            font-size: 1em;
            resize: none;
        }}
        select, button {{
            margin-top: 10px;
            width: 100%;
            padding: 10px;
            font-size: 1em;
            border-radius: 8px;
            border: none;
            background: #00c6ff;
            color: white;
            cursor: pointer;
            transition: background 0.3s ease;
        }}
        button:hover {{
            background: #0072ff;
        }}
        .result {{
            margin-top: 20px;
            font-size: 1.2em;
            word-wrap: break-word;
        }}
        .pulse {{
            display: flex;
            gap: 5px;
            margin-top: 10px;
            justify-content: center;
        }}
        .dot, .dash {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #00c6ff;
            animation: blink 1s infinite;
        }}
        .dash {{
            width: 30px;
        }}
        @keyframes blink {{
            0%, 100% {{ opacity: 0.2; }}
            50% {{ opacity: 1; }}
        }}
    </style>
</head>
<body>
    <h1>Pen Federation Morse Code Translator</h1>
    <form method="POST">
        <textarea name="data" placeholder="Enter text or Morse code...">{text}</textarea>
        <select name="mode">
            <option value="encode">Text → Morse</option>
            <option value="decode">Morse → Text</option>
        </select>
        <button type="submit">Translate</button>
    </form>
    <div class="result">{result}</div>
    <div class="pulse">
        {''.join(f'<div class="{ "dot" if c == "." else "dash" }"></div>' for c in morse if c in ".-")}
    </div>
    <form method="POST" action="/export">
        <input type="hidden" name="morse" value="{morse}">
        <button type="submit">🔊 Export Morse as WAV</button>
    </form>
</body>
</html>
"""

@app.route('/export', methods=['POST'])
def export():
    morse = request.form['morse']
    audio = morse_to_audio(morse)
    wav_file = save_wav(audio)
    return send_file(wav_file, mimetype='audio/wav', as_attachment=True, download_name='morse.wav')

if __name__ == '__main__':
    app.run(debug=True)

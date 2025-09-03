import os
import io
import wave
import struct
import math
from flask import Flask, request, send_file, render_template_string

app = Flask(__name__)

# Morse code mappings
MORSE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', ' ': '/'
}
REVERSE = {v: k for k, v in MORSE.items()}

# Audio settings
RATE, FREQ = 44100, 800
DOT, DASH, GAP = 0.1, 0.3, 0.1

def encode(text): return ' '.join(MORSE.get(c.upper(), '') for c in text)
def decode(code): return ''.join(REVERSE.get(c, '') for c in code.split())

def tone(duration): return [math.sin(2 * math.pi * FREQ * t / RATE) for t in range(int(RATE * duration))]
def silence(duration): return [0.0] * int(RATE * duration)

def morse_audio(code):
    audio = []
    for c in code:
        if c == '.': audio += tone(DOT)
        elif c == '-': audio += tone(DASH)
        elif c == ' ': audio += silence(DASH)
        audio += silence(GAP)
    return audio

def export_wav(data):
    buf = io.BytesIO()
    with wave.open(buf, 'w') as w:
        w.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
        for s in data: w.writeframes(struct.pack('h', int(s * 32767)))
    buf.seek(0)
    return buf

@app.route('/health')
def health(): return "OK", 200

@app.route('/', methods=['GET', 'POST'])
def home():
    result, morse, text = '', '', ''
    if request.method == 'POST':
        mode = request.form['mode']
        data = request.form['data']
        if mode == 'encode':
            morse = encode(data)
            result, text = morse, data
        else:
            result = decode(data)
            morse, text = data, result
    return render_template_string(TEMPLATE, result=result, morse=morse, text=text)

@app.route('/export', methods=['POST'])
def export():
    audio = morse_audio(request.form['morse'])
    return send_file(export_wav(audio), mimetype='audio/wav', as_attachment=True, download_name='morse.wav')

TEMPLATE = """
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Pen Federation Morse Code Translator</title>
<style>
body { font-family: sans-serif; background: linear-gradient(135deg,#0f2027,#203a43,#2c5364); color:white; text-align:center; padding:2em; }
form { background:rgba(255,255,255,0.1); padding:1em; border-radius:10px; max-width:400px; margin:auto; }
textarea, select, button { width:100%; margin-top:10px; padding:10px; border-radius:8px; border:none; font-size:1em; }
button { background:#00c6ff; color:white; cursor:pointer; }
button:hover { background:#0072ff; }
.pulse { display:flex; justify-content:center; gap:5px; margin-top:1em; }
.dot, .dash { width:10px; height:10px; border-radius:50%; background:#00c6ff; animation:blink 1s infinite; }
.dash { width:30px; }
@keyframes blink { 0%,100%{opacity:0.2;} 50%{opacity:1;} }
</style></head><body>
<h1>Pen Federation Morse Code Translator</h1>
<form method="POST">
<textarea name="data" placeholder="Enter text or Morse code...">{{text}}</textarea>
<select name="mode">
<option value="encode">Text → Morse</option>
<option value="decode">Morse → Text</option>
</select>
<button type="submit">Translate</button>
</form>
<div class="result">{{result}}</div>
<div class="pulse">
{% for c in morse %}{% if c == '.' %}<div class="dot"></div>{% elif c == '-' %}<div class="dash"></div>{% endif %}{% endfor %}
</div>
<form method="POST" action="/export">
<input type="hidden" name="morse" value="{{morse}}">
<button type="submit">🔊 Export Morse as WAV</button>
</form>
</body></html>
"""

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

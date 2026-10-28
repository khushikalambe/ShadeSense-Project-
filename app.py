from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import json, os, hashlib, base64, io, re
from datetime import datetime
from PIL import Image
import numpy as np
import random
from PIL import ImageDraw

def generate_ishihara_plate(number=12, size=512):
    img = Image.new('RGB', (size, size), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    center = size // 2
    radius = size // 2 - 20

    dots = []

    # Generate random dots
    for _ in range(1500):
        r = random.randint(5, 12)
        angle = random.uniform(0, 2 * np.pi)
        dist = random.uniform(0, radius)

        x = int(center + dist * np.cos(angle))
        y = int(center + dist * np.sin(angle))

        dots.append((x, y, r))

    # Create mask for number
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text((size//3, size//4), str(number), fill=255)

    mask_arr = np.array(mask)

    for x, y, r in dots:
        if 0 <= x < size and 0 <= y < size:
            if mask_arr[y, x] > 0:
                # Number color (reddish)
                color = (
                    random.randint(150, 255),
                    random.randint(50, 100),
                    random.randint(50, 100)
                )
            else:
                # Background color (greenish)
                color = (
                    random.randint(50, 120),
                    random.randint(150, 255),
                    random.randint(50, 120)
                )

            draw.ellipse((x-r, y-r, x+r, y+r), fill=color)

    return img
app = Flask(__name__)
app.secret_key = 'TrueHue_secret_2024'

DB_FILE = 'users.json'

def load_users():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE) as f:
        return json.load(f)

def save_users(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ── Routes ──────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html', user=session.get('user'))

@app.route('/register', methods=['POST'])
def register():
    d = request.json
    users = load_users()
    if d['email'] in users:
        return jsonify({'ok': False, 'msg': 'Email already registered.'})
    users[d['email']] = {
        'name': d['name'],
        'email': d['email'],
        'password': hash_pw(d['password']),
        'history': [],
        'joined': datetime.now().strftime('%Y-%m-%d')
    }
    save_users(users)
    session['user'] = {'name': d['name'], 'email': d['email']}
    return jsonify({'ok': True, 'name': d['name']})

@app.route('/login', methods=['POST'])
def login():
    d = request.json
    users = load_users()
    u = users.get(d['email'])
    if not u or u['password'] != hash_pw(d['password']):
        return jsonify({'ok': False, 'msg': 'Invalid email or password.'})
    session['user'] = {'name': u['name'], 'email': d['email']}
    return jsonify({'ok': True, 'name': u['name']})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/save_result', methods=['POST'])
def save_result():
    if 'user' not in session:
        return jsonify({'ok': False})
    d = request.json
    users = load_users()
    email = session['user']['email']
    users[email]['history'].append({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'score': d['score'],
        'total': d['total'],
        'diagnosis': d['diagnosis']
    })
    save_users(users)
    return jsonify({'ok': True})

@app.route('/get_profile')
def get_profile():
    if 'user' not in session:
        return jsonify({'ok': False})
    users = load_users()
    u = users[session['user']['email']]
    return jsonify({'ok': True, 'name': u['name'], 'email': u['email'],
                    'joined': u['joined'], 'history': u['history']})

@app.route('/correct_image', methods=['POST'])
def correct_image():
    if 'image' not in request.files:
        return jsonify({'ok': False, 'msg': 'No image'})
    
    file = request.files['image']
    mode = request.form.get('mode', 'protanopia')
    
    img = Image.open(file).convert('RGB')
    # Resize if too large
    img.thumbnail((1200, 1200), Image.LANCZOS)
    arr = np.array(img, dtype=np.float64)
    
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    if mode == 'protanopia':
        # Daltonization for protanopia - shift red channel info to green/blue
        new_r = 0.56667 * g + 0.43333 * b
        new_g = 0.55833 * g + 0.44167 * b
        new_b = b.copy()
        # Enhancement: boost contrast on remaining channels
        new_r = np.clip(new_r * 1.1, 0, 255)
        new_g = np.clip(new_g * 1.05, 0, 255)

    elif mode == 'deuteranopia':
        # Daltonization for deuteranopia
        new_r = r.copy()
        new_g = 0.625 * r + 0.375 * b
        new_b = 0.3 * r + 0.7 * b
        new_r = np.clip(new_r * 1.05, 0, 255)

    elif mode == 'tritanopia':
        # Daltonization for tritanopia
        new_r = r.copy()
        new_g = g.copy()
        new_b = -0.012245 * r + 0.511786 * g + 0.500459 * b
        new_r = np.clip(new_r, 0, 255)
        new_g = np.clip(new_g * 1.05, 0, 255)

    elif mode == 'highcontrast':
        # High contrast: amplify differences, enhance edges
        gray = 0.299 * r + 0.587 * g + 0.114 * b
        new_r = np.clip(r + (r - gray) * 0.8, 0, 255)
        new_g = np.clip(g + (g - gray) * 0.8, 0, 255)
        new_b = np.clip(b + (b - gray) * 0.8, 0, 255)

    elif mode == 'warm':
        # Warm filter - shift blues to yellows (helps some deficiencies)
        new_r = np.clip(r * 1.1, 0, 255)
        new_g = np.clip(g * 1.05, 0, 255)
        new_b = np.clip(b * 0.8, 0, 255)

    elif mode == 'cool':
        # Cool filter
        new_r = np.clip(r * 0.8, 0, 255)
        new_g = np.clip(g * 1.05, 0, 255)
        new_b = np.clip(b * 1.2, 0, 255)

    else:  # normal / simulate grayscale
        gray = 0.299 * r + 0.587 * g + 0.114 * b
        new_r = new_g = new_b = gray

    out = np.stack([
        np.clip(new_r, 0, 255).astype(np.uint8),
        np.clip(new_g, 0, 255).astype(np.uint8),
        np.clip(new_b, 0, 255).astype(np.uint8)
    ], axis=2)

    result = Image.fromarray(out, 'RGB')
    buf = io.BytesIO()
    result.save(buf, format='PNG')
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode()
    return jsonify({'ok': True, 'image': encoded, 'format': 'png'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

@app.route('/generate_plate')
def generate_plate():
    num = request.args.get('num', 12, type=int)
    img = generate_ishihara_plate(num)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    encoded = base64.b64encode(buf.read()).decode()
    return jsonify({'ok': True, 'image': encoded})
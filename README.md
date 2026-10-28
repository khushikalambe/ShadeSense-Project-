# ChromaVision — Colorblindness Testing Website

## Setup & Run

### Requirements
- Python 3.8+
- pip

### Install & Launch
```bash
pip install flask pillow numpy
python app.py
```
Then open **http://localhost:5000** in your browser.

## Features
- 🏠 **Landing page** — animated hero with live Ishihara plate previews
- 🔐 **Register / Login** — stored in `users.json` via SHA-256 hashed passwords
- ℹ️ **About page** — colorblindness types explained
- 🔴 **24-plate Ishihara test** — procedurally rendered dot-pattern plates
- 📊 **Results page** — animated score ring + full answer breakdown
- 🖼️ **Color Correction Studio** — upload image → Python/Pillow processes it server-side
- 👤 **Profile page** — test history, stats, logout
- 🌙 **Dark/Light mode** toggle

## Color Filters (server-side Python)
| Filter | Method |
|--------|--------|
| Protanopia Fix | Daltonization matrix — red channel redistributed |
| Deuteranopia Fix | Daltonization — green channel remapped |
| Tritanopia Fix | Blue channel correction matrix |
| High Contrast | Edge-enhanced color amplification |
| Warm Shift | RGB channel weight adjustment |
| Cool Shift | Blue channel boost |
| Grayscale Sim | Luminance-weighted conversion |

## File Structure
```
chromavision/
├── app.py          # Flask backend
├── templates/
│   └── index.html  # Full SPA frontend
├── users.json      # Auto-created on first registration
└── run.sh          # Quick start script
```

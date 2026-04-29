# odf-ocr

> Handschrift-OCR-Pipeline für Stundennachweise im Öffentlichen Dienst  
> **Lizenz: Apache 2.0 – kommerziell nutzbar**

## Features

- **PP-OCRv5** (PaddleOCR) als primäre OCR-Engine – Apache 2.0
- **TrOCR** (Microsoft) als Precision-Fallback bei niedrigem Konfidenzwert – MIT
- Intelligente Postprocessing-Validierung mit bekannten OCR-Korrekturen (7↔1 etc.)
- Erkennung aller OD-Kürzel (KM, KS, SV, BF, FT, KF, UR, SF, GZ, ÜZ)
- Automatisches Flagging unsicherer Felder für manuelle Prüfung
- Flask REST-API für Electron-Integration
- Vollständige Teststuite mit pytest

---

## Projektstruktur

```
odf-ocr/
├── src/odf_ocr/
│   ├── __init__.py          # Paket, Version 2.0.0
│   ├── preprocessing.py     # Bildvorverarbeitung (Skew, Binarisierung, Denoise)
│   ├── ocr_engine.py        # PaddleOCR PP-OCRv5 + TrOCR Hybrid-Engine
│   ├── layout.py            # Zeilen-/Spaltensegmentierung
│   ├── postprocessing.py    # Validierung & Fehlerkorrektur
│   ├── pipeline.py          # Hauptpipeline (TimeSheetPipeline)
│   └── server.py            # Flask REST-API (POST /ocr, GET /health)
├── electron/
│   ├── main.js              # Electron Hauptprozess
│   ├── preload.js           # Secure IPC Bridge
│   └── package.json         # Build-Config für Win/Mac/Linux
├── scripts/
│   └── start_server.py      # Server-Startskript
├── tests/
│   ├── test_postprocessing.py
│   └── test_preprocessing.py
├── docs/
│   └── architecture.md
├── README.md
├── requirements.txt
├── pyproject.toml
├── LICENSE                  # Apache 2.0
└── .gitignore
```

---

## Installation

### Python-Backend

```bash
# 1. Virtuelle Umgebung anlegen
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# 2. Abhängigkeiten installieren
pip install -r requirements.txt

# 3. Paket im Entwicklungsmodus installieren
pip install -e .
```

### Electron-Frontend

```bash
cd electron
npm install
npm run dev    # Entwicklungsmodus
npm start      # Produktionsmodus
```

---

## Schnellstart (nur Python)

```python
from odf_ocr import TimeSheetPipeline
from odf_ocr.pipeline import PipelineConfig

# Standard-Konfiguration
pipeline = TimeSheetPipeline()
result = pipeline.process("stundennachweis.jpg")

# Ergebnis ausgeben
print(result.to_json())

# Geflaggte Einträge prüfen
for entry in result.entries:
    if entry.flag:
        print(f"Zeile {entry.row_index}: {entry.flag_reason}")
```

### Server standalone starten

```bash
python scripts/start_server.py --port 5000
# → http://127.0.0.1:5000/health
```

### OCR via API

```bash
curl -X POST http://127.0.0.1:5000/ocr \
  -H "Content-Type: application/json" \
  -d '{"image": "<base64>", "filename": "nachweis.jpg"}'
```

---

## Konfiguration

```python
from odf_ocr.pipeline import PipelineConfig, TimeSheetPipeline

config = PipelineConfig(
    skew_correction=True,
    use_clahe=False,
    binarize_method="otsu",
    denoise_strength=10,
    confidence_fallback_threshold=0.70,
    enable_trocr_fallback=True,
    output_dir="./output",
)
pipeline = TimeSheetPipeline(config=config)
```

---

## Tests

```bash
pytest tests/ -v
```

---

## Lizenz-Übersicht

| Komponente | Lizenz | Kommerziell |
|---|---|---|
| PaddleOCR (PP-OCRv5) | Apache 2.0 | ✅ |
| TrOCR (microsoft/trocr-base-handwritten) | MIT | ✅ |
| OpenCV (headless) | Apache 2.0 | ✅ |
| transformers (HuggingFace) | Apache 2.0 | ✅ |
| Flask | BSD-3 | ✅ |
| odf-ocr selbst | **Apache 2.0** | ✅ |

---

## Kürzel-Referenz

| Kürzel | Bedeutung |
|---|---|
| KM | Krankheit mit AU-Schein |
| KS | Krank ohne AU-Schein |
| UR | Urlaub |
| SV | Sonderurlaub |
| BF | Berufsfortbildung |
| FT | Feiertag |
| KF | Kurzfristige Freistellung |
| SF | Sonderfreistellung |
| GZ | Gleitzeitkonto |
| ÜZ | Überzeitkonto |

---

## Mitwirken

Pull Requests willkommen. Bitte für neue Features einen Issue anlegen.

"""
server.py – Flask REST-API für Electron-Integration

Endpunkte:
  POST /ocr      – Bild hochladen, OCR starten
  GET  /health   – Statusprüfung
  POST /config   – Pipeline-Konfiguration aktualisieren
"""

from __future__ import annotations

import base64
import logging
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

from .pipeline import TimeSheetPipeline, PipelineConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

_pipeline: TimeSheetPipeline | None = None


def get_pipeline() -> TimeSheetPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = TimeSheetPipeline()
    return _pipeline


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "2.0.0"})


@app.route("/ocr", methods=["POST"])
def ocr():
    try:
        if request.is_json:
            data = request.get_json()
            img_b64 = data.get("image", "")
            filename = data.get("filename", "upload.jpg")
            img_bytes = base64.b64decode(img_b64)
        elif "file" in request.files:
            file = request.files["file"]
            filename = file.filename or "upload.jpg"
            img_bytes = file.read()
        else:
            return jsonify({"error": "Kein Bild übertragen"}), 400

        suffix = Path(filename).suffix or ".jpg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name

        pipeline = get_pipeline()
        result = pipeline.process(tmp_path)
        Path(tmp_path).unlink(missing_ok=True)
        return jsonify(result.to_dict())

    except Exception as e:
        logger.exception("Fehler in /ocr")
        return jsonify({"error": str(e)}), 500


@app.route("/config", methods=["POST"])
def update_config():
    global _pipeline
    try:
        data = request.get_json()
        config = PipelineConfig(**data)
        _pipeline = TimeSheetPipeline(config=config)
        return jsonify({"status": "Konfiguration aktualisiert"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def main(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    logger.info(f"odf-ocr Server startet auf {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()

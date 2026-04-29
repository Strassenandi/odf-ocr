#!/usr/bin/env python3
"""Startet den odf-ocr Flask-Server (aufgerufen durch Electron)."""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from odf_ocr.server import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="odf-ocr Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    main(host=args.host, port=args.port, debug=args.debug)

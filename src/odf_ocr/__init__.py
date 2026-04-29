"""
odf-ocr – Handschrift-OCR-Pipeline für Stundennachweise (Öffentlicher Dienst)
Apache 2.0 License
"""

__version__ = "2.0.0"
__author__ = "odf-ocr contributors"
__license__ = "Apache-2.0"

from .pipeline import TimeSheetPipeline

__all__ = ["TimeSheetPipeline"]

# Architektur – odf-ocr

## Überblick

```
┌─────────────────────────────────────────────────────────┐
│                    Electron Frontend                     │
│  (main.js → BrowserWindow → IPC → preload.js)           │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP (localhost:5000)
┌──────────────────────────▼──────────────────────────────┐
│                  Flask REST-API (server.py)              │
│  POST /ocr  ·  GET /health  ·  POST /config             │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│               TimeSheetPipeline (pipeline.py)           │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │preprocessing│→ │  ocr_engine  │→ │    layout     │  │
│  │    .py      │  │     .py      │  │     .py       │  │
│  └─────────────┘  └──────┬───────┘  └───────┬───────┘  │
│                          │                   │           │
│                   ┌──────▼───────────────────▼───────┐  │
│                   │      postprocessing.py             │  │
│                   │  (validate, correct, flag)         │  │
│                   └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Datenfluss

1. **Bild einlesen** → `preprocessing.preprocess()`  
2. **OCR** → `ocr_engine.HybridOCREngine.predict()`  
3. **Layout** → `layout.group_into_rows()`  
4. **Validierung** → `postprocessing.validate_all()`  
5. **Export** → `PipelineResult.to_json()`

## Erweiterbarkeit

- **Neue Kürzel**: `postprocessing.VALID_CODES` erweitern
- **Neues Formular-Layout**: `layout.COLUMN_BOUNDARIES` anpassen
- **Andere OCR-Engine**: `OCREngine`-Protokoll implementieren

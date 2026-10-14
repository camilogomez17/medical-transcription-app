"""English/Spanish medical glossary with optional imported dictionary data."""

from __future__ import annotations

import json
from pathlib import Path

# Built-in fallback terms remain available if the imported file is absent.
GLOSSARY = {
    "abdominal pain": "dolor abdominal",
    "allergy": "alergia",
    "appointment": "cita",
    "blood pressure": "presion arterial",
    "blood sugar": "azucar en la sangre",
    "blood thinner": "anticoagulante",
    "chest pain": "dolor en el pecho",
    "dizziness": "mareo",
    "dose": "dosis",
    "fever": "fiebre",
    "headache": "dolor de cabeza",
    "high blood pressure": "presion alta",
    "hypertension": "hipertension",
    "inflammation": "inflamacion",
    "insurance": "seguro medico",
    "kidney": "rinon",
    "lab results": "resultados de laboratorio",
    "medication": "medicamento",
    "nausea": "nausea",
    "pharmacy": "farmacia",
    "pregnant": "embarazada",
    "prescription": "receta",
    "rash": "sarpullido",
    "shortness of breath": "falta de aire",
    "side effect": "efecto secundario",
    "swelling": "hinchazon",
    "symptom": "sintoma",
    "treatment": "tratamiento",
    "vomiting": "vomito",
}

_IMPORTED_PATH = Path(__file__).with_name("medical_glossary.json")
if _IMPORTED_PATH.is_file():
    try:
        imported = json.loads(_IMPORTED_PATH.read_text(encoding="utf-8"))
        if isinstance(imported, dict):
            # Imported headwords take precedence over built-in entries.
            GLOSSARY.update({str(k).lower(): str(v) for k, v in imported.items()})
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Warning: could not load {_IMPORTED_PATH.name}: {exc}")


def find_terms(text: str) -> list[tuple[str, str]]:
    """Return imported/built-in English terms found in a transcript."""
    lower_text = text.casefold()
    return [
        (english, spanish)
        for english, spanish in GLOSSARY.items()
        if english in lower_text
    ]

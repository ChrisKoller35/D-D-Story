#!/usr/bin/env python3
"""
KI-Bildkarten im D&D-Stil für Hirsefurt (Kapitel 00) und Sommerhall (Kapitel 01).

Liest den Google-API-Key aus der Umgebungsvariable GOOGLE_API_KEY (oder aus
einer lokalen Datei Tools/.env mit der Zeile GOOGLE_API_KEY=...; diese Datei
ist per .gitignore ausgeschlossen und darf nie committet werden).

Ruft die Google Generative Language API auf (Gemini-Bildmodell, bei Bedarf
Imagen als Fallback) und schreibt je Karte ein PNG nach
Story/Erzaehler/Karten/.

Benötigt nur die Python-Standardbibliothek (kein pip install).

Beispiele:
    python3 Tools/karten_generieren.py                 # beide Karten
    python3 Tools/karten_generieren.py hirsefurt       # nur Hirsefurt
    python3 Tools/karten_generieren.py sommerhall --modell imagen
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

HIER = Path(__file__).resolve().parent
REPO = HIER.parent
KARTEN_ORDNER = REPO / "Story" / "Erzaehler" / "Karten"
API_BASIS = "https://generativelanguage.googleapis.com/v1beta"

# Modelle lassen sich per --gemini-modell / --imagen-modell überschreiben,
# falls Google die Namen ändert.
GEMINI_MODELL = "gemini-2.5-flash-image"
IMAGEN_MODELL = "imagen-4.0-generate-001"

STIL = (
    "Top-down fantasy tabletop RPG map in the style of a hand-drawn Dungeons & Dragons "
    "campaign map on aged parchment. Ink linework with soft watercolor washes, bird's-eye "
    "view (slightly oblique so roofs and trees are readable), warm sepia and muted earth "
    "tones, a compass rose in one corner, a decorative parchment border. Numbered markers "
    "(1, 2, 3, ...) drawn as small ink circles at the listed places, matching the legend "
    "order. No other text or labels on the map. No modern objects, no people close-up."
)

KARTEN = {
    "hirsefurt": {
        "datei": "Karte-Hirsefurt-KI.png",
        "prompt": STIL + " "
        "Subject: HIRSEFURT, a tiny sleepy farming village of about twelve timber-and-thatch "
        "houses on a small stream. Nine houses stand on the east side of the stream, three on the "
        "west side. Fields lie to the west, apple orchards around the village, chickens in the "
        "lanes. Numbered places: (1) the village square with a large old linden tree, a stone "
        "well and a wooden bench beneath the tree; (2) a small cider stand next to the square, a "
        "barrel with a plank as a counter; (3) the ford: flat stepping stones crossing the shallow "
        "stream; (4) the road leading south across the ford toward the town of Sommerhall; (5) "
        "the road coming in from the north over a low hill; (6) the apple orchards. Rolling "
        "summer meadows, nothing else: this village is deliberately small and quiet.",
    },
    "sommerhall": {
        "datei": "Karte-Sommerhall-KI.png",
        "prompt": STIL + " "
        "Subject: SOMMERHALL, a small walled medieval market town in a harvest-festival mood: "
        "garlands, pennants and market stalls. A stone town wall with a gate in the north. "
        "Numbered places: (1) the north town gate with the road leading away north toward the "
        "village of Hirsefurt; (2) a straight avenue lined with linden trees running from the gate "
        "south to the market square; (3) the large market square with a small harvest altar at "
        "its north edge and an ornate fountain with three millstones in the centre, surrounded by "
        "festival booths; (4) a great festival hall, the biggest building in town, standing on the "
        "east side of the market square: stage end to the north, large portal facing south, a row "
        "of windows facing west onto the square, a small servants' door at the back opening into "
        "an alley, and a dashed oval race track drawn around the hall; (5) a courtyard behind the "
        "hall with a cellar ramp and a barn; (6) an inn on the market square at the corner of the "
        "linden avenue, with a sickle-shaped sign; (7) three water mills on a small river in the "
        "mill quarter in the west of town; (8) a dense forest west of the town beyond the mills, "
        "with a road leading into it. The town has six districts: linden avenue, market quarter, "
        "mill quarter, tanners' lane, lower town, and farmsteads at the town edge. A faint dashed "
        "violet ring marked beneath the festival hall and half the market square (a hidden ley "
        "line node).",
    },
}


def lade_dotenv(pfad: Path) -> None:
    """Liest KEY=WERT-Zeilen aus einer .env-Datei in os.environ (ohne Überschreiben)."""
    if not pfad.is_file():
        return
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        name, wert = zeile.split("=", 1)
        name = name.strip()
        wert = wert.strip().strip('"').strip("'")
        if name and name not in os.environ:
            os.environ[name] = wert


def api_key() -> str:
    lade_dotenv(HIER / ".env")
    lade_dotenv(REPO / ".env")
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit(
            "Kein API-Key gefunden. Setze die Umgebungsvariable GOOGLE_API_KEY\n"
            "oder lege eine Datei Tools/.env mit der Zeile GOOGLE_API_KEY=... an."
        )
    return key


def post_json(url: str, key: str, daten: dict) -> dict:
    anfrage = urllib.request.Request(
        url,
        data=json.dumps(daten).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(anfrage, timeout=180) as antwort:
            return json.loads(antwort.read().decode("utf-8"))
    except urllib.error.HTTPError as fehler:
        text = fehler.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {fehler.code} von {url}:\n{text}") from None


def bild_gemini(prompt: str, key: str, modell: str) -> bytes:
    url = f"{API_BASIS}/models/{modell}:generateContent"
    daten = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }
    antwort = post_json(url, key, daten)
    for kandidat in antwort.get("candidates", []):
        for teil in kandidat.get("content", {}).get("parts", []):
            inline = teil.get("inlineData")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
    raise RuntimeError(f"Gemini lieferte kein Bild:\n{json.dumps(antwort, indent=2)[:2000]}")


def bild_imagen(prompt: str, key: str, modell: str) -> bytes:
    url = f"{API_BASIS}/models/{modell}:predict"
    daten = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": "4:3"},
    }
    antwort = post_json(url, key, daten)
    for vorhersage in antwort.get("predictions", []):
        if vorhersage.get("bytesBase64Encoded"):
            return base64.b64decode(vorhersage["bytesBase64Encoded"])
    raise RuntimeError(f"Imagen lieferte kein Bild:\n{json.dumps(antwort, indent=2)[:2000]}")


def erzeuge(name: str, args, key: str) -> Path:
    karte = KARTEN[name]
    ziel = KARTEN_ORDNER / karte["datei"]
    print(f"[{name}] erzeuge Karte ...")
    if args.modell == "imagen":
        png = bild_imagen(karte["prompt"], key, args.imagen_modell)
    else:
        try:
            png = bild_gemini(karte["prompt"], key, args.gemini_modell)
        except RuntimeError as fehler:
            print(f"[{name}] Gemini fehlgeschlagen, versuche Imagen.\n{fehler}", file=sys.stderr)
            png = bild_imagen(karte["prompt"], key, args.imagen_modell)
    KARTEN_ORDNER.mkdir(parents=True, exist_ok=True)
    ziel.write_bytes(png)
    print(f"[{name}] gespeichert: {ziel.relative_to(REPO)} ({len(png) // 1024} KB)")
    return ziel


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("karten", nargs="*", choices=[*KARTEN, []], help="hirsefurt, sommerhall (leer = beide)")
    parser.add_argument("--modell", choices=["gemini", "imagen"], default="gemini",
                        help="gemini (Standard, mit Imagen-Fallback) oder imagen")
    parser.add_argument("--gemini-modell", default=GEMINI_MODELL)
    parser.add_argument("--imagen-modell", default=IMAGEN_MODELL)
    parser.add_argument("--prompt-anzeigen", action="store_true", help="nur die Prompts ausgeben, nichts generieren")
    args = parser.parse_args()
    namen = args.karten or list(KARTEN)

    if args.prompt_anzeigen:
        for name in namen:
            print(f"=== {name} ===\n{KARTEN[name]['prompt']}\n")
        return

    key = api_key()
    for name in namen:
        erzeuge(name, args, key)


if __name__ == "__main__":
    main()

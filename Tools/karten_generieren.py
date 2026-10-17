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
    "tones, a compass rose in one corner, a decorative parchment border. Absolutely NO text "
    "on the image: no title, no letters, no numbers, no labels, no legend box, no markers. "
    "The places below are only a layout description. No modern objects, no people close-up."
)

KARTEN = {
    "hirsefurt": {
        "datei": "Karte-Hirsefurt-KI.png",
        "prompt": STIL + " "
        "Subject: HIRSEFURT, a tiny sleepy farming village of about twelve timber-and-thatch "
        "houses on a small stream. The stream flows in a gentle line straight through the village "
        "from north to south (it is NOT a ring, it does not encircle the village). Nine houses "
        "stand on the east bank, three on the west bank. Fields lie to the west, apple orchards around the village, chickens in the "
        "lanes. Layout: the village square with a large old linden tree, a stone "
        "well and a wooden bench beneath the tree; a small cider stand next to the square, a "
        "barrel with a plank as a counter; the ford: flat stepping stones crossing the shallow "
        "stream; the road leading south across the ford and out of the picture; "
        "the road coming in from the north over a low hill; the apple orchards. Rolling "
        "summer meadows, nothing else: this village is deliberately small and quiet.",
    },
    "sommerhall": {
        "datei": "Karte-Sommerhall-KI.png",
        "prompt": STIL + " "
        "Subject: SOMMERHALL, a LARGE, wealthy walled medieval city (over ten thousand "
        "inhabitants). Zoomed far out: the whole city with its wall, the surrounding farmland, "
        "the river and the forest fit inside the frame with generous open countryside around "
        "the wall, so the city itself is small enough that all of it is visible. It must look like "
        "a real city, not a village: many hundreds of densely packed houses with varied roofs, "
        "a tangle of streets, alleys and small courtyards. Harvest-festival mood: garlands, "
        "pennants, rows of market stalls. Layout and landmarks, each one clearly recognisable: "
        "(a) a GRAND MAIN GATE in the north: a huge gatehouse with two massive round towers, "
        "a barbican and a drawbridge, the most imposing part of the wall; a broad road leads "
        "north from it; (b) from the gate a broad straight avenue lined with linden trees runs "
        "south to the centre; (c) in the centre a very large market square with an ornate "
        "fountain, filled with festival booths, and several narrow winding market lanes lined "
        "with stalls radiating from it; (d) on the east side of the square the GREAT FESTIVAL "
        "HALL: an enormous, monumental hall, as large as a cathedral and many times bigger than "
        "any house, a long building with a steep roof, rows of tall windows, a grand portal to "
        "the south, a huge forecourt, an oval race track drawn around it and a walled courtyard "
        "with a barn behind; (e) at the corner of the avenue and the market square the INN "
        "'Zur Sichel': a large, distinctive timber inn with a small tower, a gallery around an "
        "inner courtyard with stables, and a big sickle-shaped sign hanging over the door, "
        "clearly standing out from the ordinary houses; (f) a magnificent TEMPLE with a tall "
        "spire, flying buttresses and a rose window, the second-largest building of the city, "
        "in the north-west quarter; (g) a BREWERY with a tall chimney, a row of big copper "
        "kettles under an open roof, stacked barrels and beer wagons in its yard, near the "
        "river; (h) a second large open square in the south of the city set up as a games "
        "field (axe-throwing lanes, a wrestling ring, tents); (i) a river crossing the west "
        "part of the city with three water mills, a mill quarter and a tanners' lane, spanned "
        "by a LARGE STONE BRIDGE with several arches and small towers at both ends; (j) a "
        "lower town with smaller houses in the south-east; farmsteads, fields and orchards "
        "outside the wall; a dense dark forest beyond the river to the west with a road leading "
        "into it. A faint dashed violet ring beneath the festival hall and half the main square "
        "(a hidden ley line node). Everything drawn only as buildings and streets, never as "
        "words or letters.",
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

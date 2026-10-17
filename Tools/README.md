# Tools

## karten_generieren.py – KI-Bildkarten (Hirsefurt, Sommerhall)

Erzeugt mit Googles Bildmodellen (Gemini-Image, Fallback Imagen) je eine
Karte im D&D-Pergament-Stil und legt sie als
`Story/Erzaehler/Karten/Karte-Hirsefurt-KI.png` und
`Story/Erzaehler/Karten/Karte-Sommerhall-KI.png` ab. Die Prompts basieren auf
den Legenden der SVG-Karten in Kapitel 00 und 01.

Braucht nur Python 3, keine zusätzlichen Pakete.

**Key hinterlegen** (nie committen): entweder als Umgebungsvariable
`GOOGLE_API_KEY`, oder in einer Datei `Tools/.env` mit der Zeile
`GOOGLE_API_KEY=dein-key` (die Datei ist per `.gitignore` ausgeschlossen).

**Ausführen:**

```bash
python3 Tools/karten_generieren.py              # beide Karten
python3 Tools/karten_generieren.py hirsefurt    # nur eine Karte (oder: sommerhall)
```

Weitere Optionen: `--modell imagen` (direkt Imagen statt Gemini),
`--prompt-anzeigen` (nur die Prompts ausgeben).

**Hinweis:** Die eingecheckten `Karte-Hirsefurt-KI.png` und `Karte-Sommerhall-KI.png`
sind eigene, extern erzeugte Bilder von Christoph (Stand 17.10.2026). Das Skript
überschreibt sie beim Lauf; nur ausführen, wenn neue Varianten gewünscht sind.

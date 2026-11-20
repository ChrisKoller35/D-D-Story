#!/usr/bin/env python3
"""
Beschriftet die Landkarte (Landkarte/Landkarte-ohne-Beschriftung.png) mit allen
Ortsnamen und schreibt Landkarte/Landkarte-<Land>.png.

Aufruf:  python3 Tools/landkarte_beschriften.py VALDOREN
Benötigt Pillow (pip install pillow) und die Schrift FreeSerif
(Debian/Ubuntu: Paket fonts-freefont-ttf). Die Schriftpfade unten anpassen,
falls sie auf dem eigenen Rechner woanders liegen.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys
land = sys.argv[1] if len(sys.argv)>1 else "VALDOREN"
HIER = Path(__file__).resolve().parent
ORDNER = HIER.parent / "Landkarte"
im = Image.open(ORDNER / "Landkarte-ohne-Beschriftung.png").convert("RGBA")
d = ImageDraw.Draw(im)
B="/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf"
I="/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf"
BI="/usr/share/fonts/truetype/freefont/FreeSerifBoldItalic.ttf"
INK=(58,42,28,255); HALO=(240,230,205,255)
def t(xy, text, font, size, fill=INK, anchor="mm", halo=3):
    f=ImageFont.truetype(font,size)
    d.text(xy,text,font=f,fill=fill,anchor=anchor,stroke_width=halo,stroke_fill=HALO)
def spaced(xy,text,font,size,gap=3,fill=INK):
    f=ImageFont.truetype(font,size)
    w=sum(f.getlength(c) for c in text)+gap*(len(text)-1); x=xy[0]-w/2
    for c in text:
        d.text((x,xy[1]),c,font=f,fill=fill,anchor="lm",stroke_width=3,stroke_fill=HALO); x+=f.getlength(c)+gap
spaced((675,42),land,B,26,gap=3)
t((895,405),"THALENDOR",B,24)
t((635,208),"Hirsefurt",B,16)
t((950,238),"Eschenbrück",B,14)
t((1165,297),"Kohlwinkel",B,14)
t((300,580),"BALDIR",B,22)
t((430,700),"Grauhorn",B,16)
t((430,717),"Hammerfeste",I,13)
t((655,290),"Mühlenwald",BI,18,fill=(40,60,38,255))
t((720,348),"Räuberlager",I,12)
t((845,438),"Mühlen",I,11)
t((790,470),"Phaes Lagerfeuer",I,12)
t((790,258),"Überfall",I,12)
t((760,185),"Rabenpass",B,14)
t((760,168),"→ Freie Städte des Nordens",I,11)
t((300,70),"R A B E N K A M M",B,15,fill=(70,70,80,255))
t((150,330),"W E S T M E E R",B,18,fill=(60,85,110,255))
t((735,240),"Silbra",BI,13,fill=(55,85,120,255))
t((1040,690),"nach Süden · Häfen nach Seranth (2 Wochen)",I,12)
t((40,748),"Hirsefurt – Thalendor: ½ Tag  ·  Thalendor – Phaes Lagerfeuer: 1 Tag  ·  Lagerfeuer – Baldir: 4 Tagesreisen  ·  Baldir – Grauhorn: 3 Meilen",I,12,anchor="lm",halo=2)
ziel = ORDNER / f"Landkarte-{land.title()}.png"
im.convert("RGB").save(ziel); print("gespeichert:", ziel)

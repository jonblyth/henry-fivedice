#!/usr/bin/env python3
"""Build the GitHub Pages site in docs/ from index.html.

index.html is written as a page fragment (no <html>/<head>), so this wraps it
in a full document, and adds the Home Screen icon and web app manifest.
Run: python3 build.py
"""
import json, math, pathlib, struct, zlib

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "docs"
OUT.mkdir(exist_ok=True)

src = (ROOT / "index.html").read_text()
head, body = src.split("<aside>", 1)
body = "<aside>" + body
head = head.replace('<meta name="apple-mobile-web-app-capable" content="yes">\n', "")

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Fivedice">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="theme-color" content="#F1F2F8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#12131C" media="(prefers-color-scheme: dark)">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" type="image/png" href="icon-192.png">
<link rel="manifest" href="manifest.webmanifest">
<style>:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
{head.strip()}
</head>
<body>
{body.strip()}
</body>
</html>
"""
(OUT / "index.html").write_text(page)

(OUT / "manifest.webmanifest").write_text(json.dumps({
    "name": "Henry Fivedice",
    "short_name": "Fivedice",
    "start_url": ".",
    "display": "standalone",
    "background_color": "#F1F2F8",
    "theme_color": "#E5484D",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
    ],
}, indent=2))


def icon(size):
    """A red die showing five white pips, drawn with 4x supersampling."""
    ss = 4
    n = size * ss
    red, white = (229, 72, 77), (255, 255, 255)
    pip_r = n * 0.085
    pips = [(0.3, 0.3), (0.7, 0.3), (0.5, 0.5), (0.3, 0.7), (0.7, 0.7)]
    pips = [(x * n, y * n) for x, y in pips]
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            acc = [0, 0, 0]
            for sy in range(ss):
                for sx in range(ss):
                    px, py = x * ss + sx + 0.5, y * ss + sy + 0.5
                    c = white if any(math.hypot(px - cx, py - cy) <= pip_r for cx, cy in pips) else red
                    for i in range(3):
                        acc[i] += c[i]
            row += bytes(v // (ss * ss) for v in acc)
        rows.append(bytes(row))
    raw = zlib.compress(b"".join(rows), 9)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", raw) + chunk(b"IEND", b""))


for name, size in [("apple-touch-icon.png", 180), ("icon-192.png", 192), ("icon-512.png", 512)]:
    (OUT / name).write_bytes(icon(size))

print("Built", OUT)

#!/usr/bin/env python
"""
AfrikaBurn Artwork Location Clicker
====================================
Loops through all 'art' entries in data.js and lets you click their
correct position on the high-res PNG map. Saves results to artwork_locations.json.

Usage:
    python artwork_clicker.py

Controls:
    - Left click  : mark the artwork location
    - Right click : skip this artwork (keep existing location)
    - u           : undo last click (go back one)
    - q           : quit and save progress
"""

import json
import re
import os
import tkinter as tk
from PIL import Image, ImageTk

# ── Config ──────────────────────────────────────────────────
DATA_JS       = os.path.expanduser("~/git_projects/afrikaburnmap-2026/www/data.js")
MAP_IMAGE     = os.path.expanduser("~/git_projects/afrikaburnmap-2026/www/afrikaburn2026-1.png")
OUTPUT_FILE   = os.path.expanduser("~/git_projects/afrikaburnmap-2026/artwork_locations.json")
DISPLAY_SCALE = 0.25   # display at 25% — adjust if too small/large
# ────────────────────────────────────────────────────────────

# Load data.js
with open(DATA_JS) as f:
    content = f.read()
match = re.search(r'const DATA_INLINE\s*=\s*(\{.*\})', content, re.DOTALL)
data = json.loads(match.group(1))

# Filter to artworks only
artworks = [e for e in data['entries'] if e['section'] == 'art']
print("Found %d artworks" % len(artworks))

# Load existing results if resuming
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE) as f:
        results = json.load(f)
    print("Resuming — %d already done" % len(results))
else:
    results = {}

# Find index to start from (first artwork not yet done)
start_idx = 0
for i, e in enumerate(artworks):
    if e['code'] not in results:
        start_idx = i
        break

# Load and scale image
print("Loading image...")
orig_img = Image.open(MAP_IMAGE)
ORIG_W, ORIG_H = orig_img.size
disp_w = int(ORIG_W * DISPLAY_SCALE)
disp_h = int(ORIG_H * DISPLAY_SCALE)
disp_img = orig_img.resize((disp_w, disp_h), Image.LANCZOS)
print("Display size: %dx%d (original: %dx%d)" % (disp_w, disp_h, ORIG_W, ORIG_H))

# ── Tkinter setup ───────────────────────────────────────────
root = tk.Tk()
root.title("AfrikaBurn Artwork Clicker")

# Info bar at top
info_frame = tk.Frame(root, bg="#222", pady=6)
info_frame.pack(fill="x")
info_label = tk.Label(info_frame, text="", bg="#222", fg="#fff",
                      font=("Helvetica", 13, "bold"), padx=12)
info_label.pack(side="left")
progress_label = tk.Label(info_frame, text="", bg="#222", fg="#aaa",
                          font=("Helvetica", 11), padx=12)
progress_label.pack(side="right")
hint_label = tk.Label(info_frame,
    text="Left click: mark location  |  Right click: skip  |  U: undo  |  Q: quit & save",
    bg="#222", fg="#888", font=("Helvetica", 10), padx=12)
hint_label.pack(side="left")

# Scrollable canvas
frame = tk.Frame(root)
frame.pack(fill="both", expand=True)

canvas = tk.Canvas(frame,
    width=min(disp_w, 1600),
    height=min(disp_h, 900),
    scrollregion=(0, 0, disp_w, disp_h),
    bg="#111", cursor="crosshair")
hbar = tk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
vbar = tk.Scrollbar(frame, orient="vertical",   command=canvas.yview)
canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
hbar.pack(side="bottom", fill="x")
vbar.pack(side="right",  fill="y")
canvas.pack(side="left", fill="both", expand=True)

photo = ImageTk.PhotoImage(disp_img)
canvas.create_image(0, 0, anchor="nw", image=photo)

# State
state = {
    'idx': start_idx,
    'marker': None,
    'old_marker': None,
    'history': []   # list of (code, x, y) for undo
}

def current_artwork():
    if state['idx'] >= len(artworks):
        return None
    return artworks[state['idx']]

def update_info():
    e = current_artwork()
    if e is None:
        info_label.config(text="All done! Press Q to save.")
        progress_label.config(text="")
        return
    remaining = len(artworks) - state['idx']
    done = len(results)
    info_label.config(text="[%s]  %s  (grid: %s)" % (e['code'], e['name'], e['grid']))
    progress_label.config(text="%d done  |  %d remaining" % (done, remaining))

    # Show existing position as a faded marker
    if state['old_marker']:
        canvas.delete(state['old_marker'])
    old_x = e.get('x', 0) * DISPLAY_SCALE
    old_y = e.get('y', 0) * DISPLAY_SCALE
    state['old_marker'] = canvas.create_oval(
        old_x-8, old_y-8, old_x+8, old_y+8,
        outline="#ff3d8a", width=2, dash=(4,4))
    # Scroll to existing position
    canvas.xview_moveto(max(0, (old_x - 400) / disp_w))
    canvas.yview_moveto(max(0, (old_y - 300) / disp_h))

def save_results():
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print("Saved %d locations to %s" % (len(results), OUTPUT_FILE))

def on_click(event):
    e = current_artwork()
    if e is None:
        return
    # Convert display coords to real image coords
    cx = canvas.canvasx(event.x)
    cy = canvas.canvasy(event.y)
    real_x = cx / DISPLAY_SCALE
    real_y = cy / DISPLAY_SCALE

    # Draw marker
    if state['marker']:
        canvas.delete(state['marker'])
    state['marker'] = canvas.create_oval(
        cx-8, cy-8, cx+8, cy+8,
        fill="#2196F3", outline="#fff", width=2)
    canvas.create_text(cx+12, cy, text=e['code'],
        fill="#fff200", font=("Helvetica", 10, "bold"), anchor="w")

    # Save
    results[e['code']] = {'x': round(real_x, 1), 'y': round(real_y, 1),
                           'name': e['name'], 'grid': e['grid']}
    state['history'].append(e['code'])
    print("  [%s] %s -> (%.0f, %.0f)" % (e['code'], e['name'], real_x, real_y))

    state['idx'] += 1
    state['marker'] = None
    # Auto-save every 10
    if len(results) % 10 == 0:
        save_results()
    update_info()

def on_skip(event):
    e = current_artwork()
    if e is None:
        return
    print("  [%s] %s -> SKIPPED" % (e['code'], e['name']))
    state['idx'] += 1
    update_info()

def on_undo(event):
    if not state['history']:
        return
    code = state['history'].pop()
    if code in results:
        del results[code]
    # Find the index of this code
    for i, e in enumerate(artworks):
        if e['code'] == code:
            state['idx'] = i
            break
    print("  Undid [%s]" % code)
    update_info()

def on_quit(event):
    save_results()
    root.quit()

canvas.bind("<Button-1>", on_click)
canvas.bind("<Button-3>", on_skip)
root.bind("<u>", on_undo)
root.bind("<U>", on_undo)
root.bind("<q>", on_quit)
root.bind("<Q>", on_quit)

update_info()
root.mainloop()
save_results()
print("Done!")

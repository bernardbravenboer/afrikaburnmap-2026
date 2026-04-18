#!/usr/bin/env python
"""
AfrikaBurn Theme Camp Location Clicker
=======================================
Loops through all 'theme' entries in data.js and lets you click their
correct position on the portrait PNG. Saves results to camp_locations.json.

Usage:
    python camp_clicker.py

Controls:
    - Left click  : mark the camp location
    - Right click : skip (keep existing location)
    - U           : undo last click
    - Q           : quit and save
"""

import json, re, os
import tkinter as tk
from PIL import Image, ImageTk

DATA_JS    = os.path.expanduser("~/git_projects/afrikaburnmap-2026/www/data.js")
MAP_IMAGE  = os.path.expanduser("~/git_projects/afrikaburnmap-2026/www/2026_map_portrait.png")
OUTPUT     = os.path.expanduser("~/git_projects/afrikaburnmap-2026/camp_locations.json")
DISPLAY_SCALE = 0.70

# Load data.js
with open(DATA_JS) as f:
    content = f.read()
match = re.search(r'const DATA_INLINE\s*=\s*(\{.*\})', content, re.DOTALL)
data = json.loads(match.group(1))

# Filter to theme camps only
camps = [e for e in data['entries'] if e['section'] == 'theme']
print("Found %d theme camps" % len(camps))

# Load existing results
if os.path.exists(OUTPUT):
    with open(OUTPUT) as f:
        results = json.load(f)
    print("Resuming — %d already done" % len(results))
else:
    results = {}

# Find start index
start_idx = 0
for i, e in enumerate(camps):
    if e['code'] not in results:
        start_idx = i
        break

# Current transform: portrait viewBox -> portrait PNG
# ax=18.257951, bx=0.014781, cx=0.4550
# ay=0.009115,  by=18.183899, cy=2.2144
def vb_to_png(vb_x, vb_y):
    px = 18.257951 * vb_x + 0.014781 * vb_y + 0.4550
    py = 0.009115  * vb_x + 18.183899 * vb_y + 2.2144
    return px, py

# Load image
print("Loading image...")
orig_img = Image.open(MAP_IMAGE)
ORIG_W, ORIG_H = orig_img.size
disp_w = int(ORIG_W * DISPLAY_SCALE)
disp_h = int(ORIG_H * DISPLAY_SCALE)
disp_img = orig_img.resize((disp_w, disp_h), Image.LANCZOS)

# Tkinter setup
root = tk.Tk()
root.title("AfrikaBurn Camp Clicker")

info_frame = tk.Frame(root, bg="#222", pady=6)
info_frame.pack(fill="x")
info_label = tk.Label(info_frame, text="", bg="#222", fg="#fff",
                      font=("Helvetica", 13, "bold"), padx=12)
info_label.pack(side="left")
progress_label = tk.Label(info_frame, text="", bg="#222", fg="#aaa",
                           font=("Helvetica", 11), padx=12)
progress_label.pack(side="right")
hint_label = tk.Label(info_frame,
    text="Left click: mark  |  Right click: skip  |  U: undo  |  Q: quit & save",
    bg="#222", fg="#888", font=("Helvetica", 10), padx=12)
hint_label.pack(side="left")

frame = tk.Frame(root)
frame.pack(fill="both", expand=True)
canvas = tk.Canvas(frame,
    width=min(disp_w, 1400), height=min(disp_h, 900),
    scrollregion=(0, 0, disp_w, disp_h), bg="#111", cursor="crosshair")
hbar = tk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
vbar = tk.Scrollbar(frame, orient="vertical",   command=canvas.yview)
canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
hbar.pack(side="bottom", fill="x")
vbar.pack(side="right",  fill="y")
canvas.pack(side="left", fill="both", expand=True)

photo = ImageTk.PhotoImage(disp_img)
canvas.create_image(0, 0, anchor="nw", image=photo)

state = {'idx': start_idx, 'marker': None, 'old_marker': None, 'history': []}

def current_camp():
    return camps[state['idx']] if state['idx'] < len(camps) else None

def update_info():
    e = current_camp()
    if e is None:
        info_label.config(text="All done! Press Q to save.")
        progress_label.config(text="")
        return
    done = len(results)
    remaining = len(camps) - state['idx']
    info_label.config(text="[%s]  %s  (grid: %s)" % (e['code'], e['name'], e['grid']))
    progress_label.config(text="%d done  |  %d remaining" % (done, remaining))

    # Show existing position as dashed pink circle
    if state['old_marker']:
        for m in state['old_marker']:
            canvas.delete(m)
    old_px, old_py = vb_to_png(e.get('x', 0), e.get('y', 0))
    dx = old_px * DISPLAY_SCALE
    dy = old_py * DISPLAY_SCALE
    m1 = canvas.create_oval(dx-10, dy-10, dx+10, dy+10, outline="#ff0000", width=2, dash=(4,4))
    # Red background label
    m2 = canvas.create_rectangle(dx+4, dy-9, dx+4+len(e['code'])*7+4, dy+9, fill="#ff0000", outline="")
    m3 = canvas.create_text(dx+8, dy, text=e['code'], fill="#ffffff", font=("Helvetica", 9, "bold"), anchor="w")
    state['old_marker'] = [m1, m2, m3]

    # Scroll to existing position
    canvas.xview_moveto(max(0, (dx - 400) / disp_w))
    canvas.yview_moveto(max(0, (dy - 300) / disp_h))

def save_results():
    with open(OUTPUT, 'w') as f:
        json.dump(results, f, indent=2)
    print("Saved %d locations to %s" % (len(results), OUTPUT))

def on_click(event):
    e = current_camp()
    if e is None:
        return
    cx = canvas.canvasx(event.x)
    cy = canvas.canvasy(event.y)
    real_x = cx / DISPLAY_SCALE
    real_y = cy / DISPLAY_SCALE
    # Convert PNG pixels back to viewBox coords
    # Inverse of: px = 18.257951*vx + 0.014781*vy + 0.4550
    #             py = 0.009115*vx  + 18.183899*vy + 2.2144
    # Simple approximation (rotation is tiny): vx = (px - cx) / ax
    vb_x = (real_x - 0.4550) / 18.257951
    vb_y = (real_y - 2.2144) / 18.183899

    if state['marker']:
        canvas.delete(state['marker'])
    state['marker'] = canvas.create_oval(cx-8, cy-8, cx+8, cy+8,
        fill="#2196F3", outline="#fff", width=2)
    canvas.create_text(cx+12, cy, text=e['code'],
        fill="#fff200", font=("Helvetica", 10, "bold"), anchor="w")

    results[e['code']] = {'x': round(vb_x, 4), 'y': round(vb_y, 4),
                           'name': e['name'], 'grid': e['grid']}
    state['history'].append(e['code'])
    print("  [%s] %s -> vb(%.2f, %.2f)" % (e['code'], e['name'], vb_x, vb_y))

    state['idx'] += 1
    state['marker'] = None
    if len(results) % 10 == 0:
        save_results()
    update_info()

def on_skip(event):
    e = current_camp()
    if e is None:
        return
    print("  [%s] SKIPPED" % e['code'])
    state['idx'] += 1
    update_info()

def on_undo(event):
    if not state['history']:
        return
    code = state['history'].pop()
    if code in results:
        del results[code]
    for i, e in enumerate(camps):
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

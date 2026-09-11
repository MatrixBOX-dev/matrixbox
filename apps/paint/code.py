import json
import math
import os
import sys

import ampule
import bitmaptools
import wifi
from check_button import check_if_button_pressed
from load_screen import (
    clearscreen,
    display,
    font_large,
    font_mini,
    font_small,
    palette,
    strlen,
    window,
)
from web_interface import footer, header

from __main__ import socket

exit_app = False
w = display.width
h = display.height

with open("interface.html") as f:
    html_body = f.read().replace("__WIDTH__", str(w)).replace("__HEIGHT__", str(h))

FONTS = {"mini": font_mini, "small": font_small, "large": font_large}

# The shared kernel `window` bitmap is 4-bit indexed (lib/load_screen.py),
# so it only ever addresses 16 colors at once no matter how they're picked.
# Every drawing route - the manual brush and the shapes below alike - speaks
# hex RGB on the wire; color_slot() is just the bit that maps a requested
# hex color onto one of those 16 physical slots, reassigning the least
# recently used one once they're all taken. #000000 is pinned to slot 0
# (the universal "black"/background convention) so it never burns a slot.
CUSTOM_SLOT_START = 1
CUSTOM_SLOT_COUNT = 15
_color_slots = {}  # hex -> slot
_color_lru = []  # hex values, oldest first


def hex_to_rgb(value: str) -> tuple:
    value = value.lstrip("#").lower()
    if len(value) != 6:
        return (255, 255, 255)

    try:
        return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))
    except ValueError:
        return (255, 255, 255)


def color_slot(value: str) -> int:
    value = value.lstrip("#").lower()
    if value in ("", "000000"):
        return 0

    if value in _color_slots:
        _color_lru.remove(value)
        _color_lru.append(value)
        return _color_slots[value]

    if len(_color_lru) < CUSTOM_SLOT_COUNT:
        slot = CUSTOM_SLOT_START + len(_color_lru)
    else:
        oldest = _color_lru.pop(0)
        slot = _color_slots.pop(oldest)

    palette[slot] = hex_to_rgb(value)
    _color_slots[value] = slot
    _color_lru.append(value)

    return slot


def _rgb_of(slot: int) -> tuple:
    c = palette[slot]
    if isinstance(c, int):
        return ((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF)

    return (c[0], c[1], c[2])


def _grid_rows():
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            r, g, b = _rgb_of(window[x, y])
            row.append(f"#{r:02x}{g:02x}{b:02x}")
        rows.append(row)

    return rows


def _apply_grid_rows(rows) -> None:
    window.fill(0)
    for y in range(min(h, len(rows))):
        for x in range(min(w, len(rows[y]))):
            cell = rows[y][x]
            if cell:
                window[x, y] = color_slot(str(cell))
    display.refresh()


def circle_points(cx: int, cy: int, r: int):
    """Midpoint circle algorithm; yields the 8-way symmetric outline points."""
    x, y = r, 0
    err = 0

    while x >= y:
        yield (cx + x, cy + y)
        yield (cx + y, cy + x)
        yield (cx - y, cy + x)
        yield (cx - x, cy + y)
        yield (cx - x, cy - y)
        yield (cx - y, cy - x)
        yield (cx + y, cy - x)
        yield (cx + x, cy - y)

        y += 1
        if err <= 0:
            err += 2 * y + 1
        if err > 0:
            x -= 1
            err -= 2 * x + 1


def draw_text(text: str, font: dict, slot: int, x0: int, y0: int) -> None:
    is_mini = font is font_mini
    fh = font["fontheight"]
    px = 0

    for ch in text:
        lookup = ch.lower() if is_mini else ch
        glyph = font.get(lookup, font.get("_"))
        if glyph is None:
            continue

        gw = glyph[0]
        for col in range(gw):
            inv = gw - col
            for row in range(fh):
                if (glyph[row + 1] >> inv) & 1:
                    x, y = x0 + px + col, y0 + row
                    if 0 <= x < w and 0 <= y < h:
                        window[x, y] = slot

        px += gw


@ampule.route("/exit", method="GET")
def paint_exit(request):
    global exit_app
    exit_app = True
    return (200, {}, """<meta http-equiv="refresh" content="0; url=../" />""")


@ampule.route("/", method="GET")
def paint_home(request):
    ip = str(wifi.radio.ipv4_address) if wifi.radio.ipv4_address else "OFFLINE"
    body = html_body.replace("__IP__", ip)
    return (200, {}, header("Paint", app=True) + body + footer())


@ampule.route("/info", method="GET")
def paint_info(request):
    return (
        200,
        {"Content-Type": "application/json"},
        json.dumps({"width": w, "height": h}),
    )


@ampule.route("/grid", method="GET")
def paint_grid(request):
    return (200, {"Content-Type": "application/json"}, json.dumps({"d": _grid_rows()}))


@ampule.route("/grid", method="POST")
def paint_set_grid(request):
    # Bulk-write counterpart to GET /grid - same {"d": rows} shape as
    # /load, minus the file. This is what the UI's undo restores through.
    try:
        data = json.loads(request.body)
        _apply_grid_rows(data["d"])
    except Exception as e:
        print("grid set err:", e)
        return (400, {}, str(e))
    return (200, {}, "ok")


@ampule.route("/background", method="POST")
def paint_background(request):
    try:
        data = json.loads(request.body)
        slot = color_slot(str(data.get("color", "#000000")))
        window.fill(slot)
        display.refresh()
    except Exception as e:
        print("background err:", e)
        return (400, {}, str(e))
    return (200, {}, "ok")


@ampule.route("/clear", method="POST")
def paint_clear(request):
    window.fill(0)
    display.refresh()
    return (200, {}, "ok")


@ampule.route("/pixel", method="POST")
def paint_pixel(request):
    try:
        data = json.loads(request.body)
        slot = color_slot(str(data.get("color", "#ffffff")))
        for pt in data["pts"]:
            x, y = int(pt[0]), int(pt[1])
            if 0 <= x < w and 0 <= y < h:
                window[x, y] = slot
        display.refresh()
    except Exception as e:
        print("pixel err:", e)
    return (200, {}, "ok")


@ampule.route("/fill", method="POST")
def paint_fill(request):
    try:
        data = json.loads(request.body)
        sx = int(data["x"])
        sy = int(data["y"])
        slot = color_slot(str(data.get("color", "#ffffff")))
        if sx < 0 or sx >= w or sy < 0 or sy >= h:
            return (200, {}, "ok")
        target = window[sx, sy]
        if target == slot:
            return (200, {}, "ok")
        stack = [(sx, sy)]
        visited = set()
        while stack:
            x, y = stack.pop()
            if (x, y) in visited:
                continue
            if x < 0 or x >= w or y < 0 or y >= h:
                continue
            if window[x, y] != target:
                continue
            visited.add((x, y))
            window[x, y] = slot
            stack.append((x + 1, y))
            stack.append((x - 1, y))
            stack.append((x, y + 1))
            stack.append((x, y - 1))
        display.refresh()
    except Exception as e:
        print("fill err:", e)
    return (200, {}, "ok")


@ampule.route("/line", method="POST")
def paint_line(request):
    try:
        data = json.loads(request.body)
        x0 = min(max(int(data["x0"]), 0), w - 1)
        y0 = min(max(int(data["y0"]), 0), h - 1)
        x1 = min(max(int(data["x1"]), 0), w - 1)
        y1 = min(max(int(data["y1"]), 0), h - 1)
        slot = color_slot(str(data.get("color", "#ffffff")))

        bitmaptools.draw_line(window, x0, y0, x1, y1, slot)
        display.refresh()
    except Exception as e:
        print("line err:", e)
        return (400, {}, str(e))
    return (200, {}, "ok")


@ampule.route("/rect", method="POST")
def paint_rect(request):
    try:
        data = json.loads(request.body)
        x0, x1 = sorted((int(data["x0"]), int(data["x1"])))
        y0, y1 = sorted((int(data["y0"]), int(data["y1"])))
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, w - 1), min(y1, h - 1)

        fill_color = data.get("fill_color")
        if fill_color:
            slot = color_slot(str(fill_color))
            bitmaptools.fill_region(window, x0, y0, x1 + 1, y1 + 1, slot)

        border_color = data.get("border_color")
        if border_color:
            slot = color_slot(str(border_color))
            bitmaptools.draw_line(window, x0, y0, x1, y0, slot)
            bitmaptools.draw_line(window, x0, y1, x1, y1, slot)
            bitmaptools.draw_line(window, x0, y0, x0, y1, slot)
            bitmaptools.draw_line(window, x1, y0, x1, y1, slot)

        display.refresh()
    except Exception as e:
        print("rect err:", e)
        return (400, {}, str(e))
    return (200, {}, "ok")


@ampule.route("/circle", method="POST")
def paint_circle(request):
    try:
        data = json.loads(request.body)
        cx, cy = int(data["x"]), int(data["y"])
        r = max(int(data["radius"]), 0)

        fill_color = data.get("fill_color")
        if fill_color:
            slot = color_slot(str(fill_color))
            for dy in range(-r, r + 1):
                y = cy + dy
                if not 0 <= y < h:
                    continue

                dx = int(math.sqrt(r * r - dy * dy))
                x0 = max(cx - dx, 0)
                x1 = min(cx + dx, w - 1)
                if x0 <= x1:
                    bitmaptools.draw_line(window, x0, y, x1, y, slot)

        border_color = data.get("border_color")
        if border_color:
            slot = color_slot(str(border_color))
            for x, y in circle_points(cx, cy, r):
                if 0 <= x < w and 0 <= y < h:
                    window[x, y] = slot

        display.refresh()
    except Exception as e:
        print("circle err:", e)
        return (400, {}, str(e))
    return (200, {}, "ok")


@ampule.route("/text", method="POST")
def paint_text(request):
    try:
        data = json.loads(request.body)
        text = str(data.get("text", ""))
        font = FONTS.get(data.get("font_size", "small"), font_small)
        slot = color_slot(str(data.get("color", "#ffffff")))
        fh = font["fontheight"]
        tw = strlen(text, font)
        padding = int(data.get("padding", 0))

        if "x" in data:
            x0 = int(data["x"])
        else:
            align = data.get("align", "left")
            if align == "center":
                x0 = max((w - tw) // 2, 0)
            elif align == "right":
                x0 = max(w - tw - padding, 0)
            else:
                x0 = padding

        if "y" in data:
            y0 = int(data["y"])
        else:
            valign = data.get("valign", "top")
            if valign == "center":
                y0 = max((h - fh) // 2, 0)
            elif valign == "bottom":
                y0 = max(h - fh - padding, 0)
            else:
                y0 = padding

        draw_text(text, font, slot, x0, y0)
        display.refresh()
    except Exception as e:
        print("text err:", e)
        return (400, {}, str(e))
    return (200, {}, "ok")


SAVE_DIR = "saves"
try:
    os.mkdir(SAVE_DIR)
except:
    pass


def _safe_name(name):
    return "".join(c for c in name if c.isalnum() or c in "_-")[:20]


@ampule.route("/saves", method="GET")
def paint_list_saves(request):
    try:
        files = [
            f.replace(".json", "") for f in os.listdir(SAVE_DIR) if f.endswith(".json")
        ]
    except:
        files = []
    return (200, {"Content-Type": "application/json"}, json.dumps(files))


@ampule.route("/save", method="POST")
def paint_save(request):
    try:
        data = json.loads(request.body)
        name = _safe_name(data["name"])
        if not name:
            return (400, {}, "bad name")
        with open(SAVE_DIR + "/" + name + ".json", "w") as f:
            json.dump({"w": w, "h": h, "d": _grid_rows()}, f)
    except Exception as e:
        print("save err:", e)
        return (500, {}, str(e))
    return (200, {}, "ok")


@ampule.route("/load", method="POST")
def paint_load(request):
    try:
        data = json.loads(request.body)
        name = _safe_name(data["name"])
        with open(SAVE_DIR + "/" + name + ".json") as f:
            img = json.load(f)
        rows = img["d"]
        _apply_grid_rows(rows)
        return (200, {"Content-Type": "application/json"}, json.dumps({"d": rows}))
    except Exception as e:
        print("load err:", e)
        return (500, {}, str(e))


@ampule.route("/delete", method="POST")
def paint_delete(request):
    try:
        data = json.loads(request.body)
        name = _safe_name(data["name"])
        os.remove(SAVE_DIR + "/" + name + ".json")
    except Exception as e:
        print("del err:", e)
    return (200, {}, "ok")


clearscreen(lines=True)
window.fill(0)
display.refresh()

try:
    while not exit_app:
        ampule.listen(socket)
        b = check_if_button_pressed()
        if b == 2:
            sys.exit()
finally:
    # The kernel only backs up/restores palette slots 0-11 on app exit, so
    # 12-15 need to be cleared by hand or a leftover custom color bleeds
    # into whatever app runs next.
    for _slot in range(12, 16):
        palette[_slot] = (0, 0, 0)

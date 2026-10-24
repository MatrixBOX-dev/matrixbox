from __main__ import *
import sys, time, gc
import load_screen
from check_button import check_if_button_pressed
from load_screen import *

microcontroller.cpu.frequency = 160000000

DISP_W = settings["width"]
DISP_H = settings["height"]

try:
    with open("stocksettings.txt") as f:
        cfg = json.loads(f.read())
except:
    cfg = {"symbols": "AAPL,MSFT,GOOG,AMZN,TSLA", "speed": 2, "interval": 60}

if "mode" not in cfg:
    cfg["mode"] = "scroll"
if "graph_range" not in cfg:
    cfg["graph_range"] = "1d"

with open("stocks.html") as f: html_body = f.read()

# palette slots: 7=green, 4=red, 5=white/grey, 0=black
palette[0] = (0, 0, 0)
palette[4] = (200, 0, 0)
palette[5] = (50, 50, 50)
palette[7] = (0, 180, 0)
palette[1] = (80, 80, 0)

quotes = []  # list of (symbol, price, change_pct)

_font_map = {"small": font_small, "large": font_large}
current_font = _font_map.get(cfg.get("font", "small"), font_small)

def _fetch_one(sym):
    """Fetch a single symbol via Yahoo chart API. Returns (price, pct) or None."""
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/" + sym + "?range=1d&interval=1d"
        resp = requests.get(url, headers={"User-Agent": "MatrixBox"})
        data = json.loads(resp.text)
        resp.close()
        meta = data["chart"]["result"][0]["meta"]
        price = meta["regularMarketPrice"]
        prev = meta["chartPreviousClose"]
        pct = ((price - prev) / prev) * 100 if prev else 0
        return (price, pct)
    except Exception as e:
        print("Fetch error for", sym, ":", e)
        try: resp.close()
        except: pass
        return None

def fetch_quotes():
    global quotes
    syms = cfg["symbols"].replace(" ", "")
    if not syms:
        return
    result = []
    for sym in syms.split(","):
        sym = sym.strip()
        if not sym:
            continue
        q = _fetch_one(sym)
        if q:
            result.append((sym, q[0], q[1]))
        gc.collect()
    quotes = result
    print("Fetched:", quotes)

def build_ticker_string():
    """Build a string like: AAPL 182.50 +1.2%  MSFT 415.20 -0.3%  ..."""
    parts = []
    for sym, price, pct in quotes:
        sign = "+" if pct >= 0 else ""
        p_str = str(price)
        # Truncate to 2 decimals
        if "." in p_str:
            whole, dec = p_str.split(".", 1)
            p_str = whole + "." + dec[:2]
        parts.append((sym.upper(), p_str, sign + "{:.1f}".format(pct) + "%", pct >= 0))
    return parts

def _safe_pset_bmp(bmp, x, y, c, bmp_w, bmp_h):
    if 0 <= x < bmp_w and 0 <= y < bmp_h:
        bmp[x, y] = c

def _draw_arrow_up(bmp, x, y, color, bmp_w, bmp_h):
    _safe_pset_bmp(bmp, x + 2, y, color, bmp_w, bmp_h)
    _safe_pset_bmp(bmp, x + 1, y + 1, color, bmp_w, bmp_h)
    _safe_pset_bmp(bmp, x + 2, y + 1, color, bmp_w, bmp_h)
    _safe_pset_bmp(bmp, x + 3, y + 1, color, bmp_w, bmp_h)
    _safe_pset_bmp(bmp, x + 2, y + 2, color, bmp_w, bmp_h)
    _safe_pset_bmp(bmp, x + 2, y + 3, color, bmp_w, bmp_h)
    _safe_pset_bmp(bmp, x + 2, y + 4, color, bmp_w, bmp_h)

def _draw_arrow_down(bmp, x, y, color, bmp_w, bmp_h):
    _safe_pset_bmp(bmp, x + 2, y, color, bmp_w, bmp_h)
    _safe_pset_bmp(bmp, x + 2, y + 1, color, bmp_w, bmp_h)
    _safe_pset_bmp(bmp, x + 2, y + 2, color, bmp_w, bmp_h)
    _safe_pset_bmp(bmp, x + 1, y + 3, color, bmp_w, bmp_h)
    _safe_pset_bmp(bmp, x + 2, y + 3, color, bmp_w, bmp_h)
    _safe_pset_bmp(bmp, x + 3, y + 3, color, bmp_w, bmp_h)
    _safe_pset_bmp(bmp, x + 2, y + 4, color, bmp_w, bmp_h)

def _render_text_to_bmp(bmp, string, start_x, y_top, color_idx, f, bmp_w, bmp_h):
    fh = f["fontheight"]
    px = start_x
    for ch in str(string):
        if ch not in f:
            ch = "_"
        glyph = f[ch]
        gw = glyph[0]
        is_bitmap = isinstance(glyph[1], int)
        if is_bitmap:
            for w in range(gw):
                sx = px + w
                if sx < 0 or sx >= bmp_w:
                    continue
                inv_w = gw - w
                for h in range(fh):
                    sy = y_top + h
                    if sy < 0 or sy >= bmp_h:
                        continue
                    bit = (glyph[h + 1] >> inv_w) & 1
                    if bit:
                        bmp[sx, sy] = color_idx
        px += gw
    return px

ticker_bmp = None
ticker_tg = None
ticker_w = 0

def build_ticker_bitmap():
    """Render all quotes into a wide bitmap. Called once when data or font changes."""
    global ticker_bmp, ticker_tg, ticker_w
    parts = build_ticker_string()
    if not parts:
        ticker_w = 0
        return

    f = current_font
    fh = f["fontheight"]
    gap = 8
    arrow_w = 6
    y_center = max(0, (DISP_H - fh) // 2)

    # Measure total width
    total_w = DISP_W  # start with padding so text scrolls in from right
    for sym, price, pct_str, up in parts:
        total_w += strlen(sym + " " + price + " ", f) + arrow_w + strlen(pct_str, f) + gap
    total_w += DISP_W  # end padding so last item scrolls fully off left

    ticker_bmp = displayio.Bitmap(total_w, DISP_H, 10)
    ticker_bmp.fill(0)

    px = DISP_W  # start drawing after initial padding
    for sym, price, pct_str, up in parts:
        color = 7 if up else 4
        px = _render_text_to_bmp(ticker_bmp, sym + " ", px, y_center, 5, f, total_w, DISP_H)
        px = _render_text_to_bmp(ticker_bmp, price + " ", px, y_center, color, f, total_w, DISP_H)
        if up:
            _draw_arrow_up(ticker_bmp, px, y_center, color, total_w, DISP_H)
        else:
            _draw_arrow_down(ticker_bmp, px, y_center, color, total_w, DISP_H)
        px += arrow_w
        px = _render_text_to_bmp(ticker_bmp, pct_str, px, y_center, color, f, total_w, DISP_H)
        px += gap

    ticker_w = total_w

    ticker_tg = displayio.TileGrid(ticker_bmp, pixel_shader=palette)
    ticker_tg.x = 0
    root = displayio.Group()
    root.append(ticker_tg)
    display.root_group = root
    gc.collect()

# ── LIST MODE ─────────────────────────────────────────────────────────────────
list_bmp = None
list_tg = None
list_h = 0
list_scroll_y = 0
ROW_PAD = 1  # 1px gap between rows

# ── GRAPH MODE ────────────────────────────────────────────────────────────────
graph_sym_idx    = 0
graph_sym        = ""
graph_closes     = []
graph_last_adv   = 0.0

# (API range, API interval) per display range label
_GRAPH_PARAMS = {
    "1d":  ("1d",  "5m"),
    "5d":  ("5d",  "15m"),
    "1mo": ("1mo", "1d"),
}

def _render_list_rows(bmp, parts, y_offset, f, bmp_w, bmp_h):
    """Render a set of quote rows starting at y_offset."""
    fh = f["fontheight"]
    row_h = fh + ROW_PAD
    for i, (sym, price, pct_str, up) in enumerate(parts):
        y = y_offset + i * row_h
        if y >= bmp_h:
            break
        color = 7 if up else 4
        px = _render_text_to_bmp(bmp, sym, 1, y, 5, f, bmp_w, bmp_h)
        px = _render_text_to_bmp(bmp, " " + price, px, y, color, f, bmp_w, bmp_h)
        arrow_w = 6
        pct_w = strlen(pct_str, f)
        right_x = bmp_w - pct_w - arrow_w - 1
        if up:
            _draw_arrow_up(bmp, right_x, y, color, bmp_w, bmp_h)
        else:
            _draw_arrow_down(bmp, right_x, y, color, bmp_w, bmp_h)
        _render_text_to_bmp(bmp, pct_str, right_x + arrow_w, y, color, f, bmp_w, bmp_h)

def build_list_bitmap():
    """Render quotes as rows into a tall bitmap for list display.
    If the list is taller than the screen, duplicate the rows plus a
    screen-height gap so vertical scrolling wraps seamlessly."""
    global list_bmp, list_tg, list_h, list_scroll_y
    parts = build_ticker_string()
    if not parts:
        list_h = 0
        return

    f = current_font
    fh = f["fontheight"]
    row_h = fh + ROW_PAD
    one_set_h = len(parts) * row_h

    if one_set_h <= DISP_H:
        # Everything fits — no scrolling needed
        total_h = DISP_H
        list_bmp = displayio.Bitmap(DISP_W, total_h, 10)
        list_bmp.fill(0)
        _render_list_rows(list_bmp, parts, 0, f, DISP_W, total_h)
        list_h = 0  # signal: no scrolling
    else:
        # Duplicate rows with a DISP_H gap for seamless wrap
        total_h = one_set_h + DISP_H + one_set_h
        list_bmp = displayio.Bitmap(DISP_W, total_h, 10)
        list_bmp.fill(0)
        _render_list_rows(list_bmp, parts, 0, f, DISP_W, total_h)
        _render_list_rows(list_bmp, parts, one_set_h + DISP_H, f, DISP_W, total_h)
        list_h = one_set_h + DISP_H  # wrap point

    list_scroll_y = 0
    list_tg = displayio.TileGrid(list_bmp, pixel_shader=palette)
    list_tg.x = 0
    list_tg.y = 0
    root = displayio.Group()
    root.append(list_tg)
    display.root_group = root
    gc.collect()

def _rebuild_current_mode():
    if cfg["mode"] == "list":
        build_list_bitmap()
    elif cfg["mode"] == "graph":
        build_graph_bitmap()
    else:
        build_ticker_bitmap()

def _fetch_history(sym):
    """Fetch closing prices for charting. Returns list of floats."""
    rng, ivl = _GRAPH_PARAMS.get(cfg.get("graph_range", "1d"), ("1d", "5m"))
    gc.collect()
    try:
        url = ("https://query1.finance.yahoo.com/v8/finance/chart/" + sym
               + "?range=" + rng + "&interval=" + ivl)
        resp = requests.get(url, headers={"User-Agent": "MatrixBox"})
        data = json.loads(resp.text)
        resp.close()
        raw = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        gc.collect()
        return [c for c in raw if c is not None]
    except Exception as e:
        print("History error", sym, ":", e)
        try: resp.close()
        except: pass
        return []

def build_graph_bitmap():
    """Render a line chart for the current symbol into a fresh bitmap."""
    global graph_sym_idx, graph_sym, graph_closes, graph_last_adv

    syms = [s.strip() for s in cfg["symbols"].replace(" ", "").split(",") if s.strip()]
    if not syms:
        return
    graph_sym_idx = graph_sym_idx % len(syms)
    sym = syms[graph_sym_idx]

    if sym != graph_sym:
        graph_closes = _fetch_history(sym)
        graph_sym = sym
    graph_last_adv = time.monotonic()

    f        = font_small
    fh       = f["fontheight"]
    lbl_h    = fh + 1       # pixels for top label
    chart_y0 = lbl_h
    chart_h  = DISP_H - lbl_h
    chart_w  = DISP_W

    bmp = displayio.Bitmap(DISP_W, DISP_H, 10)
    bmp.fill(0)

    closes = graph_closes
    if not closes or len(closes) < 2:
        _render_text_to_bmp(bmp, sym + " no data", 1, 0, 5, f, DISP_W, DISP_H)
    else:
        mn = min(closes)
        mx = max(closes)
        if mx == mn:
            mx = mn + 0.001

        up         = closes[-1] >= closes[0]
        line_color = 7 if up else 4
        pct        = ((closes[-1] - closes[0]) / closes[0]) * 100 if closes[0] else 0
        sign       = "+" if pct >= 0 else ""
        rng_label  = cfg.get("graph_range", "1d")
        label      = sym + " " + sign + "{:.1f}".format(pct) + "% " + rng_label
        _render_text_to_bmp(bmp, label, 1, 0, line_color, f, DISP_W, DISP_H)

        def py(p):
            return chart_y0 + int((mx - p) / (mx - mn) * (chart_h - 1))

        # Dim baseline at opening price
        base_y = py(closes[0])
        if chart_y0 <= base_y < DISP_H:
            for xi in range(chart_w):
                if bmp[xi, base_y] == 0:
                    bmp[xi, base_y] = 5  # gray

        # Line chart — connect adjacent Y values vertically to avoid gaps
        n      = len(closes)
        prev_y = None
        for xi in range(chart_w):
            ci = xi * (n - 1) // max(chart_w - 1, 1)
            y  = py(closes[ci])
            if prev_y is not None:
                y0 = min(prev_y, y)
                y1 = max(prev_y, y)
                for yy in range(y0, y1 + 1):
                    if chart_y0 <= yy < DISP_H:
                        bmp[xi, yy] = line_color
            else:
                if chart_y0 <= y < DISP_H:
                    bmp[xi, y] = line_color
            prev_y = y

    tg = displayio.TileGrid(bmp, pixel_shader=palette)
    root = displayio.Group()
    root.append(tg)
    display.root_group = root
    display.refresh()
    gc.collect()


@ampule.route("/", method="GET")
def stock_interface(request):
    return (200, {}, header("Stocks", app=True) + html_body + footer())

@ampule.route("/exit", method="GET")
def exit_interface(request):
    load_settings.app_running = False
    return (200, {}, """<meta http-equiv="refresh" content="0; url=../" />""")

@ampule.route("/settings", method="GET")
def get_settings(request):
    return (200, {}, json.dumps(cfg))

@ampule.route("/quotes", method="GET")
def get_quotes(request):
    return (200, {}, json.dumps(quotes))

@ampule.route("/", method="POST")
def stock_post(request):
    global cfg
    print("POST:", request.params)
    rebuild = False
    if "symbols" in request.params:
        cfg["symbols"] = ampule.url_decoder(request.params["symbols"]).upper()
        fetch_quotes()
        rebuild = True
    if "speed" in request.params:
        try: cfg["speed"] = int(request.params["speed"])
        except: pass
    if "interval" in request.params:
        try: cfg["interval"] = int(request.params["interval"])
        except: pass
    if "font" in request.params:
        global current_font
        cfg["font"] = request.params["font"]
        current_font = _font_map.get(cfg["font"], font_small)
        rebuild = True
    if "mode" in request.params:
        cfg["mode"] = request.params["mode"]
        rebuild = True
    if "graph_range" in request.params and request.params["graph_range"] in ("1d","5d","1mo"):
        cfg["graph_range"] = request.params["graph_range"]
        if cfg["mode"] == "graph":
            global graph_sym
            graph_sym = ""  # force re-fetch on next build
            rebuild = True
    if rebuild:
        _rebuild_current_mode()
    if "save" in request.params:
        try:
            with open("stocksettings.txt", "w") as f:
                f.write(json.dumps(cfg))
        except: pass
    return (200, {}, "ok")

# Main loop
fetch_quotes()
_rebuild_current_mode()
last_fetch     = time.monotonic()
graph_last_adv = time.monotonic()
speed_map = {1: 0.06, 2: 0.03, 3: 0.015}

while load_settings.app_running:
    spd = speed_map.get(cfg.get("speed", 2), 0.03)

    if cfg["mode"] == "list":
        if list_tg and list_h > 0:
            # Seamless continuous scroll
            list_scroll_y += 1
            if list_scroll_y >= list_h:
                list_scroll_y = 0
            list_tg.y = -list_scroll_y
            display.refresh()
        elif list_tg:
            display.refresh()
        else:
            pprint("no data", 0)
    elif cfg["mode"] == "graph":
        # Static display; advance symbol after dwell period
        dwell = cfg.get("graph_dwell", 8)
        if time.monotonic() - graph_last_adv >= dwell:
            syms = [s.strip() for s in cfg["symbols"].replace(" ","").split(",") if s.strip()]
            graph_sym_idx = (graph_sym_idx + 1) % max(1, len(syms))
            graph_sym = ""  # force re-fetch
            build_graph_bitmap()
        spd = 0.1  # no need for fast loop in static graph mode
    else:
        if ticker_tg and ticker_w > 0:
            ticker_tg.x -= 1
            if ticker_tg.x < -ticker_w + DISP_W:
                ticker_tg.x = 0
            display.refresh()
        else:
            pprint("no data", 0)

    time.sleep(spd)
    ampule.listen(socket)

    b = check_if_button_pressed()
    if b == 1:
        # Cycle scroll → list → graph → scroll
        _modes = ["scroll", "list", "graph"]
        cur = cfg["mode"] if cfg["mode"] in _modes else "scroll"
        cfg["mode"] = _modes[(_modes.index(cur) + 1) % len(_modes)]
        if cfg["mode"] == "graph":
            graph_sym = ""  # force fresh fetch on entry
        _rebuild_current_mode()
    elif b == 2:
        load_settings.app_running = False

    # Periodic refresh
    if time.monotonic() - last_fetch > cfg.get("interval", 60):
        fetch_quotes()
        if cfg["mode"] != "graph":
            _rebuild_current_mode()
        last_fetch = time.monotonic()
        gc.collect()

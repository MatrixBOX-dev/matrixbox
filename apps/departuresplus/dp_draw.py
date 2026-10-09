# Departures Plus - everything that touches the LED matrix.
#
# Layers, bottom to top: two content bitmaps (so a page change can scroll),
# a black band for the status row, the ticker (a wide bitmap moved by x),
# clock/date, the page indicator and black masks over the side margins.
# Blinking is a palette swap, not a redraw, so every blinking row stays in step.
from __main__ import display
import time
import displayio, bitmaptools
from load_screen import font_mini, font_small, font_large
import dp_cfg

C_TONE = 1; C_DIM = 2; C_FAINT = 3; C_RED = 4; C_REDDIM = 5; C_WHITE = 6; C_BLINK = 7; C_BOXW = 8; C_BOXWB = 9; C_TICK = 10
C_L1 = 11; C_L2 = 12; C_L3 = 13       # the parts of an animated real-time mark
C_BOXWD = 14                          # a dimmed white signet
C_LINE0 = 15
NCOL = 96          # 27 line colours, each as normal / dim / blinking

TONES = {"amber": (1.0, 0.4, 0.0), "orange": (1.0, 0.22, 0.0), "yellow": (1.0, 0.6, 0.0), "white": (0.45, 0.45, 0.45),
         "warm": (0.7, 0.42, 0.18), "red": (1.0, 0.0, 0.0), "green": (0.1, 1.0, 0.1), "blue": (0.05, 0.25, 1.0),
         "cyan": (0.0, 0.8, 0.9), "pink": (1.0, 0.05, 0.45)}


CLOCK7 = (0b0011100, 0b0101010, 0b1001001, 0b1001101, 0b1000001, 0b0100010, 0b0011100)
CLOCK5 = (0b01110, 0b10101, 0b10111, 0b10001, 0b01110)


def _glyph(font, ch, low):
    if low: ch = ch.lower()
    g = font.get(ch)
    if g is None: g = font.get("_")
    return g


# Real-time marks. The digits are the parts that light up one after the other when animated.
LIVE = {"wave": (("33300", "00030", "22003", "00203", "10203"), ("330", "003", "103")),      # waves from the bottom left corner
        "dot": (("11", "11"), ("11", "11")),
        "bar": (("33", "33", "22", "22", "11", "11"), ("3", "2", "2", "1", "1"))}
APPROX = ("01000", "10101", "00010")


def tw(font, s):
    low = font is font_mini
    w = 0
    for ch in s:
        g = _glyph(font, ch, low)
        w += g[0] if g else 4
    return w - 1 if w else 0


def text(bmp, font, s, x, y, c, x0=0, x1=None, fh=0):
    """Draws s at x,y in palette index c, clipped to columns x0..x1. Returns the next x."""
    W = bmp.width; H = bmp.height
    if x1 is None or x1 > W: x1 = W
    if x0 < 0: x0 = 0
    if not fh: fh = font["fontheight"]
    low = font is font_mini
    for ch in s:
        g = _glyph(font, ch, low)
        if g is None:
            x += 4
            continue
        gw = g[0]
        if x + gw > x0 and x < x1:
            n = len(g) - 1
            if n > fh: n = fh
            top = 1 << (gw - 1)
            for r in range(n):
                row = g[r + 1]
                if not row or not isinstance(row, int): continue
                yy = y + r
                if yy < 0 or yy >= H: continue
                m = top; xx = x
                while m:
                    if row & m and x0 <= xx < x1: bmp[xx, yy] = c
                    m >>= 1; xx += 1
        x += gw
    return x


def fit(font, s, avail, abbr=dp_cfg.ABBR):
    if tw(font, s) <= avail: return s
    for a, b in abbr:
        if a in s:
            s = s.replace(a, b)
            if tw(font, s) <= avail: return s
    return s


def _hex_rel(h, soften=0.35):
    # Monitor colour -> relative LED drive. LEDs are close to linear, a monitor is not.
    # A fully normalised colour looks neon on the panel, so dark colours stay a little darker.
    if isinstance(h, str):
        try: h = int(h.replace("#", ""), 16)
        except Exception: h = 0xFF9900
    c = [(((h >> 16) & 255) / 255) ** 1.8, (((h >> 8) & 255) / 255) ** 1.8, ((h & 255) / 255) ** 1.8]
    m = max(c[0], c[1], c[2], 0.001) ** (1 - soften)
    return min(1.0, c[0] / m), min(1.0, c[1] / m), min(1.0, c[2] / m)


class Screen:
    def __init__(self, cfg):
        self.FW = display.width
        self.H = display.height
        self.pal = displayio.Palette(NCOL)
        self.slots = {}
        self.next_slot = C_LINE0
        self.group = None
        self.blink_on = True
        self.anim = ("wave", 3)
        self.build(cfg)

    # ---- palette -------------------------------------------------------
    def _lv(self, r, g, b, k=1.0):
        # The panel shows 16 levels per channel, so colours are picked as whole levels.
        L = self.L * k
        v = [int(r * L + 0.5), int(g * L + 0.5), int(b * L + 0.5)]
        if not (v[0] or v[1] or v[2]) and (r or g or b):
            m = max(r, g, b)
            v = [1 if c == m else 0 for c in (r, g, b)]
        return (v[0] * 17, v[1] * 17, v[2] * 17)

    def set_palette(self, cfg):
        self.L = 3 * max(1, min(3, int(cfg["brightness"])))
        self.dim_k = 0.4 if self.L >= 6 else 0.67
        t = TONES.get(cfg["tone"])
        if t is None:
            t = _hex_rel(cfg.get("tone_hex", "#ff9900"), 0.0)
            s = t[0] + t[1] + t[2]
            if s > 1.5: t = (t[0] * 1.5 / s, t[1] * 1.5 / s, t[2] * 1.5 / s)   # keep white-ish tones from drawing too much power
        self.tone = t
        p = self.pal
        inv = cfg.get("invert", 0)          # the whole panel lit, the text dark
        p[0] = self._lv(t[0], t[1], t[2]) if inv else (0, 0, 0)
        p[C_TONE] = (0, 0, 0) if inv else self._lv(t[0], t[1], t[2])
        p[C_DIM] = self._lv(t[0], t[1], t[2], self.dim_k)
        p[C_FAINT] = self._lv(t[0], t[1], t[2], 0.3 if self.L >= 6 else 0.67)
        p[C_RED] = self._lv(1, 0, 0)
        p[C_REDDIM] = self._lv(1, 0, 0, self.dim_k)
        p[C_WHITE] = self._lv(0.5, 0.5, 0.5)
        p[C_BOXW] = self._lv(0.75, 0.75, 0.75)
        p[C_BOXWD] = self._lv(0.75, 0.75, 0.75, self.dim_k)
        p[C_TICK] = p[C_TONE] if (inv or cfg.get("ticker_color") == "tone") else p[C_WHITE]
        for rgb in self.slots: self._fill_slot(rgb, self.slots[rgb])
        self.set_blink(self.blink_on)
        self.set_anim(self.anim[0], self.anim[1])

    def _fill_slot(self, rgb, i):
        r, g, b = _hex_rel(rgb)
        self.pal[i] = self._lv(r, g, b)
        self.pal[i + 1] = self._lv(r, g, b, self.dim_k)
        self.pal[i + 2] = self.pal[i] if self.blink_on else self.pal[0]

    def line_slot(self, rgb):
        i = self.slots.get(rgb)
        if i is None:
            if self.next_slot + 2 >= NCOL:
                self.slots = {}
                self.next_slot = C_LINE0
            i = self.next_slot
            self.next_slot += 3
            self.slots[rgb] = i
            self._fill_slot(rgb, i)
        return i

    def set_blink(self, on):
        self.blink_on = on
        p = self.pal
        p[C_BLINK] = p[C_TONE] if on else p[0]
        p[C_BOXWB] = p[C_BOXW] if on else p[0]
        for rgb in self.slots:
            i = self.slots[rgb]
            p[i + 2] = p[i] if on else p[0]

    # ---- layers --------------------------------------------------------
    def build(self, cfg):
        FW = self.FW; H = self.H
        ml = max(0, int(cfg.get("margin_l", 0))); mr = max(0, int(cfg.get("margin_r", 0)))
        if FW - ml - mr < 32: ml = mr = 0
        W = FW - ml - mr
        self.W = W; self.ml = ml
        f = cfg["font"]
        self.pitch = 6 if f == "compact" else 13 if f == "large" else 8
        self.font = font_mini if f == "compact" else font_large if f == "large" else font_small
        self.fh = 5 if f == "compact" else 12 if f == "large" else 8
        if cfg["status"] != "off":
            n = max(1, (H - 6) // self.pitch)
            band = H - n * self.pitch
        else:
            n = max(1, H // self.pitch)
            band = 0
        self.n = n; self.band = band; self.ch = H - band
        self.spare = H - band - n * self.pitch
        self.set_palette(cfg)
        self.abbr = dp_cfg.pairs(cfg.get("abbr", "")) + list(dp_cfg.ABBR)

        g = displayio.Group()
        self.cur = displayio.Bitmap(W, self.ch, NCOL)
        self.nxt = displayio.Bitmap(W, self.ch, NCOL)
        self.tg_cur = displayio.TileGrid(self.cur, pixel_shader=self.pal, x=ml, y=0)
        self.tg_nxt = displayio.TileGrid(self.nxt, pixel_shader=self.pal, x=ml, y=H)
        g.append(self.tg_cur); g.append(self.tg_nxt)
        self.tick_group = displayio.Group()
        self.left_group = displayio.Group()
        self.tick_items = []; self.tick_segs = []; self.tick_bmps = {}
        self.tick_last = None; self.tick_i = 0
        s = str(cfg.get("ticker_sep", "+++")).strip()
        self.tick_sep = ("   " + s + "   ") if s else "     "
        self.tick_gap = not cfg.get("ticker_gapless", 1)
        self.left_w = 0; self.left = None
        if band:
            self.sfont = font_small if band >= 8 else font_mini
            self.sh = 8 if band >= 8 else 6
            self.sy = H - self.sh
            g.append(displayio.TileGrid(displayio.Bitmap(FW, band, 2), pixel_shader=self.pal, x=0, y=self.ch))
            g.append(self.tick_group)
            g.append(self.left_group)
        self.pg_group = displayio.Group()
        g.append(self.pg_group)
        if ml: g.append(displayio.TileGrid(displayio.Bitmap(ml, H, 2), pixel_shader=self.pal, x=0, y=0))
        if mr: g.append(displayio.TileGrid(displayio.Bitmap(mr, H, 2), pixel_shader=self.pal, x=FW - mr, y=0))
        self.pg = None; self.pg_key = None
        self.only = False
        self.group = g
        display.root_group = g

    def power(self, mode):
        """0 = dark, 1 = everything, 2 = only the ticker (a message that wakes a switched-off display)."""
        full = mode == 1
        self.only = mode == 2
        self.group.hidden = mode == 0
        self.tg_cur.hidden = not full
        self.tg_nxt.hidden = not full
        self.left_group.hidden = not full
        self.pg_group.hidden = not full
        display.refresh()

    # ---- content -------------------------------------------------------
    def signet(self, bmp, x, y, w, h, label, f, fh, rgb, pill, state=0, ink="auto", inv=False):
        """state: 0 normal, 1 dim, 2 blinking. inv: a white box with the name in the line's colour."""
        if inv:
            slot = C_BOXWB if state == 2 else C_BOXWD if state == 1 else C_BOXW
            if rgb == dp_cfg.TONE_BOX: c = C_BLINK if state == 2 else C_DIM if state == 1 else C_TONE
            else: c = self.line_slot(rgb) + state
        elif rgb == dp_cfg.TONE_BOX:
            slot = C_BLINK if state == 2 else C_DIM if state == 1 else C_TONE
            c = 0
        else:
            slot = self.line_slot(rgb) + state
            if ink == "auto":
                lum = (0.299 * ((rgb >> 16) & 255) + 0.587 * ((rgb >> 8) & 255) + 0.114 * (rgb & 255)) / 255
                ink = "black" if lum > 0.5 else "white"
            c = 0 if ink == "black" else (C_BOXWB if state == 2 else C_BOXW)
        bitmaptools.fill_region(bmp, x, y, x + w, y + h, slot)
        if pill:
            bmp[x, y] = 0; bmp[x + w - 1, y] = 0; bmp[x, y + h - 1] = 0; bmp[x + w - 1, y + h - 1] = 0
        text(bmp, f, label, x + (w - tw(f, label)) // 2, y + (h - fh) // 2, c)

    def icon(self, bmp, rows, x, y, c=0):
        """c = 0 draws each part in its own animated colour."""
        for dy in range(len(rows)):
            m = rows[dy]
            for i in range(len(m)):
                if m[i] != "0" and 0 <= x + i < bmp.width and 0 <= y + dy < bmp.height:
                    bmp[x + i, y + dy] = c or (C_L1 + ord(m[i]) - 49)

    def set_anim(self, kind, p):
        """p: 0..2 while animated, 3 = everything lit."""
        self.anim = (kind, p)
        t = self.pal[C_TONE]
        if kind == "dot":
            self.pal[C_L1] = self.pal[C_DIM] if p == 2 else t       # pulses
        else:
            self.pal[C_L1] = t                                      # builds up
            self.pal[C_L2] = t if p >= 1 else self.pal[0]
            self.pal[C_L3] = t if p >= 2 else self.pal[0]

    def draw_rows(self, bmp, rows, cfg):
        bmp.fill(0)
        W = self.W; f = self.font; fh = self.fh
        big = cfg["font"] == "large"
        inv = cfg["badge"] == "invert"
        use_fill = cfg["badge"] in ("fill", "invert") and cfg["font"] != "compact"
        sf = font_small if big else font_mini
        boxh = 9 if big else 7
        sfh = 7 if big else 5
        bm = cfg["blink"]
        ink = cfg.get("badge_ink", "auto")
        colw = tW = dW = gW = 0
        for r in rows:
            w = tw(sf, r["line"]) + 4 if (use_fill and r["rgb"] is not None) else tw(f, r["line"])
            if w > colw: colw = w
            w = tw(f, r["time"])
            if w > tW: tW = w
            if r["dly"]:
                w = tw(f, r["dly"])
                if w > dW: dW = w
            if r["tag"]:
                w = tw(f, r["tag"])
                if w > gW: gW = w
        n = int(cfg.get("line_col", 0))
        if n:       # a steady column, so destinations start at the same place on every station
            boxed = use_fill and any(r["rgb"] is not None for r in rows)
            w = tw(sf, "0" * n) + 4 if boxed else tw(f, "0" * n)
            if w > colw: colw = w
        gap = 2 if W <= 64 else 3
        lv = cfg.get("live", "off")
        cap = 5 if f is font_mini else (12 if big else 7)          # height of a capital letter
        ic = LIVE[lv][1 if cap < 7 else 0] if lv in LIVE else None
        dx = colw + int(cfg.get("gap", gap))
        y = 0
        for r in rows:
            dimmed = r["dim"]
            T = C_DIM if dimmed else C_TONE
            bk = r["blink"] and not dimmed
            state = 2 if (bk and bm in ("line", "row")) else 1 if dimmed else 0
            rgb = r["rgb"]
            if rgb is None: text(bmp, f, r["line"], 0, y, C_BLINK if state == 2 else T, fh=fh)
            elif use_fill: self.signet(bmp, 0, y, colw, boxh, r["line"], sf, sfh, rgb, r["pill"], state, ink, inv)
            elif rgb == dp_cfg.TONE_BOX: text(bmp, f, r["line"], 0, y, C_BLINK if state == 2 else T, fh=fh)
            else: text(bmp, f, r["line"], 0, y, self.line_slot(rgb) + state, fh=fh)
            right = W
            ts = r["time"]
            if ic:      # a mark behind the time of real-time departures
                iw = len(ic[0])
                if r["live"] and not r["canc"]:
                    self.icon(bmp, ic, W - iw, y + ((cap - 2) // 2 if lv == "dot" else cap - len(ic)), C_DIM if dimmed else 0)
                right -= iw + 2
            if ts:
                c = C_RED if r["canc"] else (C_BLINK if bk and bm in ("time", "row") else T)
                text(bmp, f, ts, right - tw(f, ts), y, c, fh=fh)
                if lv == "tick" and ts[-1] == "'" and r["live"] and c == C_TONE:      # the minute mark of a real-time departure pulses
                    text(bmp, f, "'", right - tw(f, "'"), y, C_L1, fh=fh)
                if lv == "approx" and not r["live"] and not r["canc"]:      # a "~" in front of timetable times
                    self.icon(bmp, APPROX, right - tw(f, ts) - 6, y + (cap - 3) // 2, C_DIM)
            if lv == "approx" and tW: right -= 6
            if tW: right -= tW + gap
            if dW:
                if r["dly"]: text(bmp, f, r["dly"], right - tw(f, r["dly"]), y, T if cfg.get("delay_color") == "tone" else (C_REDDIM if dimmed else C_RED), fh=fh)
                right -= dW + gap
            if gW:
                text(bmp, f, r["tag"], right - tw(f, r["tag"]), y, C_FAINT, fh=fh)
                right -= gW + gap
            text(bmp, f, fit(f, r["dest"], right - 1 - dx, self.abbr), dx, y, C_BLINK if bk and bm in ("dest", "row") else T, x0=dx, x1=right - 1, fh=fh)
            y += self.pitch

    def spinner(self, bmp, k):
        """Three dots in the top right corner, one of them lit: something is loading."""
        for i in range(3):
            x = self.W - 10 + i * 4
            bitmaptools.fill_region(bmp, x, 0, x + 2, 2, C_TONE if i == k % 3 else C_FAINT)

    def draw_message(self, bmp, lines):
        # lines: [(text, palette index)], small type, top left
        bmp.fill(0)
        def wrap(f):                        # a text too long for one line wraps at its spaces
            out = []
            for t, c in lines:
                cur = ""
                for w in t.split(" "):
                    n = (cur + " " + w) if cur else w
                    if cur and tw(f, n) > self.W:
                        out.append((cur, c))
                        cur = w
                    else: cur = n
                out.append((cur, c))
            return out
        out = wrap(font_small)
        f = font_small
        if 8 * len(out) > self.ch or any(tw(font_small, t) > self.W for t, c in out):
            f = font_mini
            out = wrap(f)
        p = 8 if f is font_small else 6
        y = 0
        for t, c in out[:max(1, self.ch // p)]:
            text(bmp, f, t, 0, y, c)
            y += p

    def draw_intro(self, bmp, name, lines, walk_long, walk_short, cfg):
        """lines: [(label, rgb or None, pill)]"""
        bmp.fill(0)
        W = self.W; ch = self.ch
        ink = cfg.get("badge_ink", "auto")
        cands = [(font_large, 12), (font_small, 8), (font_mini, 6)]
        fits = [c for c in cands if tw(c[0], name) <= W - 2]
        if not fits:
            name = fit(font_mini, name, W - 2, self.abbr)
        pick = None
        for c in fits:
            if c[1] + 9 <= ch:
                pick = c
                break
        if pick is None:
            for c in fits:
                if c[1] <= ch:
                    pick = c
                    break
        if pick is None: pick = cands[2]
        f, cap = pick
        badges = ch >= cap + 9 and len(lines) > 0
        total = cap + (9 if badges else 0)
        y0 = max(0, (ch - total) // 2)
        nw = tw(f, name)
        text(bmp, f, name, max(1, (W - nw) // 2), y0, C_TONE, fh=cap)
        if not badges: return
        by = y0 + cap + 2
        widths = [tw(font_mini, l[0]) + 4 for l in lines]
        tot = sum(widths) + 2 * (len(widths) - 1)
        while tot > W - 2 and len(widths) > 1:
            widths.pop()
            tot = sum(widths) + 2 * (len(widths) - 1)
        wt = ""
        if walk_long and tot + 5 + tw(font_mini, walk_long) <= W - 2: wt = walk_long
        elif walk_short and tot + 5 + tw(font_mini, walk_short) <= W - 2: wt = walk_short
        x = (W - (tot + (5 + tw(font_mini, wt) if wt else 0))) // 2
        for i in range(len(widths)):
            label, rgb, pill = lines[i]
            if rgb is None: text(bmp, font_mini, label, x + 2, by + 1, C_TONE)
            else: self.signet(bmp, x, by, widths[i], 7, label, font_mini, 5, rgb, pill, 0, ink, cfg["badge"] == "invert")
            x += widths[i] + 2
        if wt: text(bmp, font_mini, wt, x + 3, by + 1, C_DIM)

    def flip(self, kind, on_frame=None):
        """Shows what was drawn into self.nxt. kind: scroll (up), down, left, right or random; anything else cuts."""
        ml = self.ml
        if kind == "random":
            kind = ("scroll", "down", "left", "right", "dissolve", "blinds", "wipe")[(time.monotonic_ns() // 1000000) % 7]
        if kind in ("dissolve", "blinds", "wipe"):
            self._pieces(kind, on_frame)
            return
        if kind in ("scroll", "down", "left", "right"):
            side = kind in ("left", "right")
            span = self.W if side else self.ch
            sg = -1 if kind in ("scroll", "left") else 1
            steps = 10
            for i in range(1, steps + 1):
                p = 1 - i / steps
                off = span - int(span * p * p * p + 0.5)
                if side:
                    self.tg_nxt.y = 0
                    self.tg_cur.x = ml + sg * off
                    self.tg_nxt.x = ml + sg * (off - span)
                else:
                    self.tg_cur.y = sg * off
                    self.tg_nxt.y = sg * (off - span)
                if on_frame: on_frame()
                display.refresh()
                time.sleep(0.02)
        self._swap()

    def _pieces(self, kind, on_frame):
        """Copies the new page over the old one piece by piece: small tiles in a scattered order (dissolve),
        stripes that widen (blinds) or a curtain from the left (wipe). The same bitmap stays on screen."""
        W = self.W; ch = self.ch
        cur = self.cur; nxt = self.nxt
        def put(x, y, x2, y2):
            bitmaptools.blit(cur, nxt, x, y, x1=x, y1=y, x2=min(W, x2), y2=min(ch, y2))
        def frame():
            if on_frame: on_frame()
            display.refresh()
            time.sleep(0.02)
        if kind == "dissolve":
            nx = (W + 3) // 4
            n = nx * ((ch + 3) // 4)
            st = 37 if n % 37 else 41          # a stride that visits every tile once, far apart
            per = max(1, n // 12)
            for i in range(n):
                j = (i * st) % n
                put((j % nx) * 4, (j // nx) * 4, (j % nx) * 4 + 4, (j // nx) * 4 + 4)
                if i % per == per - 1: frame()
        elif kind == "blinds":
            for s in range(8):
                for x in range(s, W, 8): put(x, 0, x + 1, ch)
                frame()
        else:
            for x in range(0, W, 8):
                put(x, 0, x + 8, ch)
                frame()
        display.refresh()

    def roll(self, px, on_frame=None):
        """self.nxt holds the old page moved up by px: both travel that far, so the rows slide up."""
        step = 1 if px <= 13 else 2
        for off in range(step, px + 1, step):
            self.tg_cur.y = -off
            self.tg_nxt.y = px - off
            if on_frame: on_frame()
            display.refresh()
            time.sleep(0.02)
        self._swap()

    def _swap(self):
        self.cur, self.nxt = self.nxt, self.cur
        self.tg_cur, self.tg_nxt = self.tg_nxt, self.tg_cur
        self.tg_cur.x = self.ml; self.tg_cur.y = 0
        self.tg_nxt.x = self.ml; self.tg_nxt.y = self.H

    # ---- status row ----------------------------------------------------
    def set_left(self, a, b, icon=False):
        """Clock (a) and date (b) at the left of the status row, optionally with a clock symbol."""
        if not self.band: return
        f = self.sfont
        ic = (CLOCK7 if self.sh == 8 else CLOCK5) if icon else None
        w = len(ic) + 2 if ic else 0
        if a: w += tw(f, a) + 4
        if b: w += tw(f, b) + 4
        if w != self.left_w:
            while len(self.left_group): self.left_group.pop()
            self.left = None
            self.left_w = w
            if w:
                self.left = displayio.Bitmap(w, self.sh, NCOL)
                self.left_group.append(displayio.TileGrid(self.left, pixel_shader=self.pal, x=self.ml, y=self.sy))
        if self.left is None: return
        self.left.fill(0)
        x = 0
        if ic:
            n = len(ic)
            for j in range(n):
                for i in range(n):
                    if ic[j] >> (n - 1 - i) & 1: self.left[i, j] = C_FAINT
            x = n + 2
        if a: x = text(self.left, f, a, x, 0, C_TONE) + 3
        if b: text(self.left, f, b, x, 0, C_FAINT)

    def set_ticker(self, items, reset=False):
        """items: the texts that take turns in the ticker. It is an endless belt: each text comes in from the right
        behind the one before it. A text that is dropped just does not come round again, a new one joins the round."""
        if not self.band: return
        self.tick_items = items
        if reset:
            while len(self.tick_group): self.tick_group.pop()
            self.tick_segs = []
        keep = items + [s[2] for s in self.tick_segs]
        for k in list(self.tick_bmps):
            if k not in keep: del self.tick_bmps[k]

    def step_ticker(self):
        segs = self.tick_segs
        it = self.tick_items
        if not segs and not it: return False
        for s in segs: s[0].x -= 1
        if segs and segs[0][0].x + segs[0][1] <= self.ml + (0 if self.only else self.left_w):
            self.tick_group.pop(0)       # scrolled out at the left
            segs.pop(0)
        x = segs[-1][0].x + segs[-1][1] if segs else self.ml + self.W
        if it and x <= self.ml + self.W:
            i = (it.index(self.tick_last) + 1) if self.tick_last in it else self.tick_i
            i %= len(it)
            if self.tick_gap and i == 0 and segs: return True       # not endless: a round leaves before the next one starts
            t = it[i]
            self.tick_last = t; self.tick_i = i
            b = self.tick_bmps.get(t)
            if b is None:
                s = t + self.tick_sep
                b = displayio.Bitmap(min(tw(self.sfont, s), 1600), self.sh, NCOL)
                text(b, self.sfont, s, 0, 0, C_TICK)
                self.tick_bmps[t] = b
            tg = displayio.TileGrid(b, pixel_shader=self.pal, x=x, y=self.sy)
            self.tick_group.append(tg)
            segs.append([tg, b.width, t])
        return True

    def set_pager(self, mode, n, cur, prog=0.0, pages=1, page=0):
        """mode: dots | bar (the current station is a small bar that fills up) | off.
        With several pages the current station's dot becomes one small mark per page."""
        W = self.W; H = self.H
        if mode == "off" or (n < 2 and pages < 2):
            if self.pg is not None:
                while len(self.pg_group): self.pg_group.pop()
                self.pg = None; self.pg_key = None
            return
        wide = 8 if mode == "bar" else (pages * 2 - 1 if pages > 1 else 2)
        w = (n - 1) * 4 + wide
        key = (mode, n, pages)
        if self.pg_key != key:
            while len(self.pg_group): self.pg_group.pop()
            if self.band:
                # as tall as the status row and opaque, so the ticker passes underneath
                self.pg = displayio.Bitmap(w + 3, self.sh, NCOL)
                x = W - w - 3; y = self.sy
            else:
                hh = 2 if self.spare >= 2 else 1
                self.pg = displayio.Bitmap(w, hh, NCOL)
                x = (W - w) // 2; y = H - hh
            self.pg_group.append(displayio.TileGrid(self.pg, pixel_shader=self.pal, x=self.ml + x, y=y))
            self.pg_key = key
        b = self.pg
        b.fill(0)
        pad = b.width - w
        y0 = 2 if self.band else 0
        y1 = y0 + (2 if self.band else b.height)
        x = pad
        for i in range(n):
            if i == cur and mode == "bar":
                fill = int(wide * prog + 0.5)
                bitmaptools.fill_region(b, x, y0, x + wide, y1, C_FAINT)
                if fill: bitmaptools.fill_region(b, x, y0, x + fill, y1, C_TONE)
                x += wide + 2
            elif i == cur and pages > 1:
                for k in range(pages):
                    bitmaptools.fill_region(b, x + k * 2, y0, x + k * 2 + 1, y1, C_TONE if k == page else C_DIM)
                x += wide + 2
            else:
                bitmaptools.fill_region(b, x, y0, x + 2, y1, C_TONE if i == cur else C_FAINT)
                x += 4

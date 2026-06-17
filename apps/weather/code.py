from __main__ import *
import sys, time, random, math, bitmaptools
import load_screen
from check_button import check_if_button_pressed

microcontroller.cpu.frequency = 240000000

W = display.width
H = display.height
_fh = font_mini["fontheight"]   # 5 px
TEMP_Y = H - _fh - 1            # y position for temperature text row

# ── Palette ───────────────────────────────────────────────────────────────────
# Indices 0-11 follow pprint _color_map so text helpers work correctly.
# Temperature text uses color="white" → palette[5] = pure white.
# Animation bg uses indices 12-18 so they never conflict with text colors.
palette[0]  = (0,   0,   0)      # black / off
palette[1]  = (120, 100,  0)     # yellow  – sun core
palette[2]  = (90,  92, 100)     # lt-grey – light cloud
palette[3]  = (10,  35,  80)     # blue    – deeper sky
palette[4]  = (80,  10,  10)     # red     – (dynamic: beach/winter/lightning)
palette[5]  = (120, 120, 120)    # white   – temp/text
palette[6]  = (20,  50,  80)     # lt-blue – clear sky bg
palette[7]  = (0,   60,  10)     # green   – (dynamic: beach/winter)
palette[8]  = (40,  42,  48)     # grey    – dark cloud
palette[9]  = (0,    0,   0)     # black2  – (dynamic: beach/winter)
palette[10] = (80,  25,  35)     # pink    – (dynamic: beach/winter/fog)
palette[11] = (120,  55,   0)    # orange  – sun glow/rays
palette[12] = (15,  40,  75)     # deeper sky (partly cloudy bg / snow bg)
palette[13] = (6,    8,  14)     # very dark storm sky
palette[14] = (55,  58,  65)     # medium grey cloud
palette[15] = (40,  60, 100)     # rain drop – (dynamic: snow→snowflake)

# ── Config ────────────────────────────────────────────────────────────────────
try:
    with open("weathersettings.txt") as f:
        cfg = json.loads(f.read())
except Exception:
    cfg = {}

for k, v in [("city", ""), ("lat", 0.0), ("lon", 0.0), ("unit", "C"), ("interval", 300), ("clock", 0), ("clockmode", "24")]:
    if k not in cfg:
        cfg[k] = v

# ── HTML (using shared design system from web_interface.py) ───────────────────
_CONTENT = """
<div class="card">
<div class="section-title">Current Weather</div>
<div style="text-align:center;padding:14px 0">
<div id="wt" style="font-size:2.4rem;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">--</div>
<div id="wc" style="font-size:.95rem;color:var(--muted);margin-top:8px">Loading...</div>
<div id="wl" style="font-size:.75rem;color:var(--muted);margin-top:4px;opacity:.65"></div>
</div>
<div id="msg" style="font-size:.82rem;color:#ff7070;text-align:center;min-height:18px"></div>
<button class="btn btn-full" onclick="rf()">&#8635; Refresh Now</button>
</div>
<div class="card">
<div class="section-title">Location</div>
<label>City name</label>
<div style="display:flex;gap:8px">
<input type="text" id="city" placeholder="e.g. Stockholm">
<button class="btn" onclick="sc()">Set</button>
</div>
</div>
<div class="card">
<div class="section-title">Temperature Unit</div>
<div class="action-row" style="margin-top:8px">
<button class="btn btn-ghost" id="uc" onclick="su('C')">°C Celsius</button>
<button class="btn btn-ghost" id="uf" onclick="su('F')">°F Fahrenheit</button>
</div>
</div>
<div class="card">
<div class="section-title">Show Clock</div>
<div class="action-row" style="margin-top:8px">
<button class="btn btn-ghost" id="ckon" onclick="stk(1)">On</button>
<button class="btn btn-ghost" id="ckoff" onclick="stk(0)">Off</button>
</div>
</div>
<div class="card">
<div class="section-title">Clock Format</div>
<div class="action-row" style="margin-top:8px">
<button class="btn btn-ghost" id="cm24" onclick="scm('24')">24h</button>
<button class="btn btn-ghost" id="cm12" onclick="scm('12')">12h AM/PM</button>
</div>
</div>
<div class="card">
<div class="section-title">Auto-refresh Interval</div>
<div class="action-row" style="margin-top:8px">
<button class="btn btn-ghost" onclick="si(60)">1 min</button>
<button class="btn btn-ghost" onclick="si(300)">5 min</button>
<button class="btn btn-ghost" onclick="si(600)">10 min</button>
</div>
</div>
<button class="btn btn-full" style="margin-top:4px" onclick="sv()">&#128190; Save Settings</button>
<script>
function p(d,cb){fetch("/?"+d,{method:"POST"}).then(function(r){return r.json()}).then(function(j){if(cb)cb(j)}).catch(function(){})}
function sc(){var c=document.getElementById("city").value.trim();if(!c)return;p("city="+encodeURIComponent(c),function(j){var m=document.getElementById("msg");if(j.error){m.textContent=j.error;}else{m.textContent="";lw();}})}
function su(u){p("unit="+u);uh(u)}
function uh(u){document.getElementById("uc").style.opacity=u==="C"?"1":"0.4";document.getElementById("uf").style.opacity=u==="F"?"1":"0.4";}
function stk(v){p("clock="+v);ckh(v)}
function ckh(v){document.getElementById("ckon").style.opacity=v?"1":"0.4";document.getElementById("ckoff").style.opacity=v?"0.4":"1";}
function scm(m){p("clockmode="+m);cmh(m)}
function cmh(m){document.getElementById("cm24").style.opacity=m==="24"?"1":"0.4";document.getElementById("cm12").style.opacity=m==="12"?"1":"0.4";}
function si(n){p("interval="+n)}
function sv(){p("save=1")}
function rf(){p("refresh=1",function(){lw()})}
function lw(){fetch("/weather").then(function(r){return r.json()}).then(function(d){var t=document.getElementById("wt");if(d.temp!==null&&d.temp!==undefined){var u=d.unit==="F"?"°F":"°C";t.textContent=d.temp.toFixed(1)+u;}else{t.textContent="--";}document.getElementById("wc").textContent=d.desc||"--";document.getElementById("wl").textContent=d.city||"";}).catch(function(){})}
function ls(){fetch("/settings").then(function(r){return r.json()}).then(function(d){if(d.city)document.getElementById("city").value=d.city;uh(d.unit||"C");ckh(d.clock||0);cmh(d.clockmode||"24");}).catch(function(){})}
ls();lw();setInterval(lw,20000);
</script>
"""

try:
    html = header("Weather", app=True) + _CONTENT + footer()
except Exception as _e:
    print("HTML build error:", _e)
    html = "<html><body><h2>Weather</h2><a href='/exit'>Exit</a></body></html>"

_DEBUG_CONTENT = """
<div class="card">
<div class="section-title">Scene Debug</div>
<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px">
<button class="btn btn-ghost" onclick="dm('beach')">Beach</button>
<button class="btn btn-ghost" onclick="dm('winter')">Winter</button>
<button class="btn btn-ghost" onclick="dm('clear_day')">Clear Day</button>
<button class="btn btn-ghost" onclick="dm('clear_night')">Clear Night</button>
<button class="btn btn-ghost" onclick="dm('partly_cloudy')">Partly Cloudy</button>
<button class="btn btn-ghost" onclick="dm('cloudy')">Cloudy</button>
<button class="btn btn-ghost" onclick="dm('rain')">Rain</button>
<button class="btn btn-ghost" onclick="dm('drizzle')">Drizzle</button>
<button class="btn btn-ghost" onclick="dm('storm')">Storm</button>
<button class="btn btn-ghost" onclick="dm('fog')">Fog</button>
<button class="btn btn-ghost" onclick="dm('snow')">Snow</button>
</div>
<div id="ds" style="font-size:.85rem;color:var(--muted);margin-top:10px;text-align:center"></div>
</div>
<div style="text-align:center;margin-top:8px"><a href="/" style="color:var(--accent)">Back to settings</a></div>
<script>
function dm(m){fetch("/debug?mode="+m,{method:"POST"}).then(function(r){return r.json()}).then(function(j){document.getElementById("ds").textContent="Active: "+j.mode}).catch(function(){})}
</script>
"""
try:
    _DEBUG_HTML = header("Debug", app=True) + _DEBUG_CONTENT + footer()
except Exception:
    _DEBUG_HTML = "<html><body><h2>Debug</h2></body></html>"

# ── Weather state ─────────────────────────────────────────────────────────────
weather_code = -1
temperature  = None
condition    = "clear"
status_msg   = ""
last_fetch   = -9999.0
utc_offset   = 0
server_epoch = 0       # epoch seconds parsed from API current.time
server_mono  = 0.0     # monotonic timestamp when server_epoch was captured
sunrise_epoch = 0      # today's sunrise as epoch (local)
sunset_epoch  = 0      # today's sunset  as epoch (local)

_WMO_DESC = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Rain showers", 81: "Heavy showers", 82: "Violent showers",
    85: "Snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Storm + hail", 99: "Heavy storm",
}

def wmo_to_cond(code):
    if code <= 1:               return "clear"
    if code == 2:               return "partly_cloudy"
    if code == 3:               return "cloudy"
    if code in (45, 48):        return "fog"
    if 51 <= code <= 55:        return "drizzle"
    if (61 <= code <= 65) or (80 <= code <= 82): return "rain"
    if (71 <= code <= 77) or code in (85, 86):   return "snow"
    if code >= 95:              return "storm"
    return "clear"

# ── Animation state ───────────────────────────────────────────────────────────
frame          = 0
exit_app       = False
clouds         = []    # [x_f, y, w, c_idx]
particles      = []    # [x_f, y_f, vx, vy]  rain / snow
birds          = []    # [x_f, y, phase_f, spd]
bolt_path      = []    # [(x, y), ...] precomputed lightning bolt
lightning_age  = 9999  # frames since last lightning strike
next_lightning = 120   # frame number for next strike (updated by init_scene)

# ── Pixel helpers ─────────────────────────────────────────────────────────────
SKY_H = TEMP_Y  # animation area stops above temperature text

# Checker palette colors and their dimmed solid-fill equivalents
_CHECKER_COLORS = {6: (20, 50, 80), 12: (15, 40, 75), 3: (10, 35, 80), 13: (6, 8, 14), 10: (60, 62, 68)}
_SOLID_COLORS  = {6: (10, 25, 40), 12: (8, 20, 38), 3: (5, 18, 40), 13: (3, 4, 7), 10: (30, 31, 34)}
# Night variants (very dark / near-black)
_NIGHT_CHECKER = {6: (3, 5, 18), 12: (2, 4, 15), 3: (2, 4, 15), 13: (3, 3, 8), 10: (15, 15, 20)}
_NIGHT_SOLID   = {6: (0, 0, 0), 12: (0, 0, 0), 3: (0, 0, 0), 13: (0, 0, 0), 10: (0, 0, 0)}

def _is_night():
    """Return True if current time is before sunrise or after sunset."""
    if not server_epoch or not sunrise_epoch or not sunset_epoch:
        return False
    now = server_epoch + int(time.monotonic() - server_mono)
    return now < sunrise_epoch or now >= sunset_epoch

def _is_beach():
    """Return True for beach scene: clear sky, daytime, temp > 23°C."""
    return (condition == "clear" and temperature is not None
            and temperature > 23 and not _is_night())

def _is_winter():
    """Return True for winter scene: snow + below freezing."""
    return (condition == "snow" and temperature is not None
            and temperature < 0)

def _sky_checker(c):
    """Checkerboard fill of the sky area only — half the lit pixels."""
    colors = _NIGHT_CHECKER if _is_night() else _CHECKER_COLORS
    if c in colors:
        palette[c] = colors[c]
    window.fill(0)
    for y in range(SKY_H):
        start = y % 2
        for x in range(start, W, 2):
            window[x, y] = c

def _sky_solid(c):
    """Solid fill of the sky area with dimmed palette color."""
    colors = _NIGHT_SOLID if _is_night() else _SOLID_COLORS
    if c in colors:
        palette[c] = colors[c]
    window.fill(0)
    bitmaptools.fill_region(window, 0, 0, W, SKY_H, c)

def _sp(x, y, c):
    xi, yi = int(x), int(y)
    if 0 <= xi < W and 0 <= yi < H:
        window[xi, yi] = c

def _fill(x, y, w, h, c):
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(W, x + w), min(H, y + h)
    if x2 > x1 and y2 > y1:
        bitmaptools.fill_region(window, x1, y1, x2, y2, c)

# ── Drawing helpers ───────────────────────────────────────────────────────────
def draw_cloud(x, y, w, c):
    """3-bump cloud blob at pixel position (x, y) with given width w."""
    bh = max(3, w // 5)
    _fill(x,                  y + 2, w,      bh, c)  # main body
    hw = max(2, w // 3)
    _fill(x + 1,              y + 1, hw,      2, c)  # left bump
    _fill(x + w // 2 - 1,    y,     hw + 1,  2, c)  # centre bump (tallest)
    _fill(x + w - hw - 1,    y + 1, hw,      2, c)  # right bump

def draw_moon(frame_n):
    """Crescent moon in warm yellow."""
    palette[1] = (120, 110, 30)   # warm yellow moon
    r  = min(5, H // 7)
    cx = W - r - 4
    cy = r + 2
    # Draw crescent: full disc minus offset shadow disc
    sr = r
    sx = cx - r // 3
    sy = cy - 1
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                # Skip pixels inside the shadow disc
                ddx = (cx + dx) - sx
                ddy = (cy + dy) - sy
                if ddx * ddx + ddy * ddy <= sr * sr:
                    continue
                _sp(cx + dx, cy + dy, 1)

def draw_beach(frame_n):
    """Beach scene: sand, sea with gentle waves, parasol."""
    # Set beach palette colors dynamically
    palette[4]  = (100, 15, 15)   # parasol red
    palette[7]  = (110, 90, 30)   # sand
    palette[9]  = (15,  50, 90)   # sea water
    palette[10] = (60,  30, 10)   # parasol pole (brown)

    sea_y  = SKY_H * 2 // 3       # where sea meets sand
    sand_y = SKY_H - 3             # sand starts here (few rows)

    # Sea (below sky, above sand)
    bitmaptools.fill_region(window, 0, sea_y, W, sand_y, 9)

    # Gentle wave line at top of sea
    for x in range(W):
        wv = int(math.sin(frame_n * 0.06 + x * 0.25) * 1.2)
        _sp(x, sea_y + wv, 5)      # white foam
        if wv < 0:
            _sp(x, sea_y + wv + 1, 9)

    # Sand
    bitmaptools.fill_region(window, 0, sand_y, W, SKY_H, 7)

    # ── Parasol ───────────────────────────────────────────────────────────
    px = W // 4                    # parasol center x
    pole_top = sand_y - 7          # top of pole
    pole_bot = sand_y              # bottom of pole (on sand)
    pr = max(4, W // 10)           # parasol canopy radius

    # Pole
    for y in range(pole_top, pole_bot + 1):
        _sp(px, y, 10)

    # Canopy: half-circle with red/white stripes
    for dy in range(0, pr + 1):        # only top half (dy <= 0 from center)
        for dx in range(-pr, pr + 1):
            if dx * dx + dy * dy <= pr * pr:
                # Stripe: divide by angle-ish columns
                stripe = ((dx + pr) * 4) // (2 * pr + 1)
                c = 4 if stripe % 2 == 0 else 5   # red / white
                _sp(px + dx, pole_top - dy, c)
    # Canopy bottom edge
    for dx in range(-pr, pr + 1):
        if dx * dx <= pr * pr:
            _sp(px + dx, pole_top, 4)

def draw_winter(frame_n):
    """Winter scene: white ground, red house, pine trees, snowman."""
    # Dynamic palette
    palette[4]  = (90,  12,  12)   # red – house walls
    palette[7]  = (8,   45,  12)   # dark green – tall tree
    palette[9]  = (20,  55,  20)   # lighter green – small tree
    palette[10] = (50,  28,   8)   # brown – trunk / door
    palette[11] = (120, 100,  20)  # warm yellow – window glow
    palette[1]  = (110,  50,   0)  # orange – carrot nose

    ground_y = SKY_H - 2           # ground is 2 px tall

    # ── Red house (right side) ─────────────────────────────────
    hx = W * 3 // 5
    hw = max(10, W // 5)
    hh = max(7, SKY_H // 4)
    hy = ground_y - hh
    roof_h = max(3, hh // 3)

    # Walls
    _fill(hx, hy, hw, hh, 4)

    # Roof (black triangle – narrow at peak, wide at eaves)
    cx_h = hx + hw // 2
    for row in range(roof_h):
        span = (row + 1) * hw // (2 * roof_h)
        ry = hy - roof_h + row
        for x in range(cx_h - span, cx_h + span + 1):
            _sp(x, ry, 0)
    # Snow on roof peak
    for row in range(min(2, roof_h)):
        span = (row + 1) * hw // (2 * roof_h)
        ry = hy - roof_h + row
        for x in range(cx_h - span, cx_h + span + 1):
            _sp(x, ry, 5)

    # Chimney
    ch_x = cx_h + hw // 4
    ch_top = hy - roof_h - max(2, roof_h // 2)
    ch_bot = hy - roof_h + roof_h // 2
    for cy in range(ch_top, ch_bot + 1):
        _sp(ch_x, cy, 0)
        _sp(ch_x + 1, cy, 0)

    # Window (left side, glowing)
    wy = hy + hh // 3
    ww = max(2, hw // 5)
    wh = max(2, hh // 4)
    wx = hx + hw // 5
    _fill(wx, wy, ww, wh, 11)

    # Door (right side, brown, sits on ground)
    dw = max(2, hw // 6)
    dh = max(3, hh // 2)
    dx0 = hx + hw * 3 // 5
    _fill(dx0, ground_y - dh, dw, dh, 10)

    # ── Tall pine tree (left-center) ─────────────────────────────
    _draw_pine(W * 2 // 5, ground_y, max(8, SKY_H // 3), 7)

    # ── Small pine tree (far left) ──────────────────────────────
    _draw_pine(W // 7, ground_y, max(5, SKY_H // 5), 9)

    # ── Snowman (left quarter) ──────────────────────────────────
    sx = W // 4
    br = max(3, SKY_H // 10)
    by = ground_y - br
    # Body
    for dy in range(-br, br + 1):
        for dx in range(-br, br + 1):
            if dx * dx + dy * dy <= br * br:
                _sp(sx + dx, by + dy, 5)
    # Head
    hr = max(2, br * 2 // 3)
    head_y = by - br - hr
    for dy in range(-hr, hr + 1):
        for dx in range(-hr, hr + 1):
            if dx * dx + dy * dy <= hr * hr:
                _sp(sx + dx, head_y + dy, 5)
    # Eyes
    _sp(sx - 1, head_y - 1, 0)
    _sp(sx + 1, head_y - 1, 0)
    # Carrot nose
    _sp(sx, head_y, 1)
    _sp(sx + 1, head_y, 1)
    # Buttons
    _sp(sx, by - br // 2, 0)
    _sp(sx, by, 0)
    _sp(sx, by + br // 2, 0)
    # Arms (sticks)
    for i in range(1, br + 1):
        _sp(sx - br - i, by - br // 2 + i // 2, 10)
        _sp(sx + br + i, by - br // 2 + i // 2, 10)

    # ── Ground (drawn LAST so nothing covers it) ──────────────
    palette[5] = (120, 120, 120)   # white – snow patches
    palette[14] = (30,  50,  80)   # light blue – ground base
    bitmaptools.fill_region(window, 0, ground_y, W, ground_y + 2, 14)
    # Snowy patches – pseudo-random using x hash for stable pattern
    for x in range(W):
        h = (x * 137 + 53) % 97
        if h % 5 < 2:                     # ~40% coverage
            _sp(x, ground_y, 5)
        if h % 7 < 1:                     # some on bottom row too
            _sp(x, ground_y + 1, 5)

def _draw_pine(cx, ground_y, h, color):
    """Draw a pine tree at cx with given height. Snow on tips."""
    trunk_h = max(2, h // 4)
    canopy_h = h - trunk_h
    tree_top = ground_y - h
    # Trunk
    for y in range(ground_y - trunk_h, ground_y):
        _sp(cx, y, 10)
    # Canopy: triangle widening downward
    for row in range(canopy_h):
        y = tree_top + row
        half_w = (row * (canopy_h // 3 + 2)) // canopy_h
        for dx in range(-half_w, half_w + 1):
            _sp(cx + dx, y, color)
        # Snow on edges and top
        if row < 2 or row % 3 == 0:
            _sp(cx - half_w, y, 5)
            _sp(cx + half_w, y, 5)
    # Snow cap on top
    _sp(cx, tree_top, 5)
    _sp(cx, tree_top + 1, 5)

def draw_sun(frame_n):
    """Animated sun with core, glow ring, and alternating rays."""
    palette[1] = (120, 100, 0)    # restore sun-core yellow
    r  = min(5, H // 7)
    cx = W - r - 4
    cy = r + 2
    # Glow ring (orange)
    for dy in range(-r - 1, r + 2):
        for dx in range(-r - 1, r + 2):
            d2 = dx * dx + dy * dy
            if r * r < d2 <= (r + 1) * (r + 1):
                _sp(cx + dx, cy + dy, 11)
    # Core (yellow)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                _sp(cx + dx, cy + dy, 1)
    # Animated rays (8 directions, alternate every 6 frames)
    phase = (frame_n // 6) % 2
    for i, (rdx, rdy) in enumerate([(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]):
        rl = 2 if (i + phase) % 2 == 0 else 1
        for l in range(1, rl + 1):
            _sp(cx + rdx * (r + 1 + l), cy + rdy * (r + 1 + l), 11)

def draw_bird(bx, by, phase):
    """5-pixel V-shaped bird silhouette with flapping wings."""
    # wings-up when int(phase*2)%4 < 2, wings-level otherwise
    wy = -1 if int(phase * 2) % 4 < 2 else 0
    _sp(bx - 2, by + wy, 8)  # left tip
    _sp(bx - 1, by,      8)  # left inner
    _sp(bx,     by + 1,  8)  # body
    _sp(bx + 1, by,      8)  # right inner
    _sp(bx + 2, by + wy, 8)  # right tip

def draw_text(text, x, y, c):
    """Render text with font_mini directly to window at pixel position (x, y)."""
    text = text.lower()
    px = x
    for ch in text:
        if ch not in font_mini:
            ch = "_"
        g  = font_mini[ch]
        gw = g[0]
        if isinstance(g[1], int):
            for w in range(gw):
                inv_w = gw - w
                for h in range(_fh):
                    if (g[h + 1] >> inv_w) & 1:
                        _sp(px + w, y + h, c)
        px += gw
    return px

def text_width(text):
    text = text.lower()
    w = 0
    for ch in text:
        if ch not in font_mini:
            ch = "_"
        w += font_mini[ch][0]
    return w

# ── Scene initialisation ──────────────────────────────────────────────────────
def init_scene(cond):
    global particles, clouds, birds, bolt_path, lightning_age, next_lightning
    particles     = []
    clouds        = []
    birds         = []
    bolt_path     = []
    lightning_age = 9999
    next_lightning = frame + random.randint(60, 120)

    if cond in ("clear", "partly_cloudy"):
        n_birds = 1 if _is_night() else 3
        for _ in range(n_birds):
            birds.append([
                float(random.randint(-W, W)),
                float(random.randint(3, max(4, H // 2 - 8))),
                random.uniform(0.0, 6.28),
                random.uniform(0.25, 0.55),
            ])
        if cond == "partly_cloudy":
            # One cloud drifting in front of the sun
            clouds.append([float(random.randint(W // 3, W - 10)), 2.0, 12, 2])

    elif cond in ("cloudy", "fog"):
        # cloudy = white/bright clouds on deep blue; fog = white wisps on grey
        c_idx = 2 if cond == "cloudy" else 5
        for _ in range(4):
            clouds.append([
                float(random.randint(-12, W)),
                float(random.randint(1, H // 3)),
                random.randint(10, 18),
                c_idx,
            ])

    elif cond in ("drizzle", "rain", "storm"):
        c_idx = 8 if cond == "storm" else 14
        for _ in range(3):
            clouds.append([
                float(random.randint(0, max(1, W - 20))),
                float(random.randint(0, 5)),
                random.randint(16, 24),
                c_idx,
            ])
        n_drops = 40 if cond == "storm" else (22 if cond == "rain" else (5 if cond == "drizzle" else 10))
        for _ in range(n_drops):
            vy = random.uniform(1.5, 2.8)
            vx = -vy * 0.18
            particles.append([
                float(random.randint(0, W - 1)),
                float(random.randint(-H, 0)),
                vx, vy,
            ])

    elif cond == "snow":
        clouds.append([float(random.randint(0, W - 16)), 0.0, 14, 14])
        clouds.append([float(random.randint(0, W - 14)), 2.0, 12, 8])
        for _ in range(20):
            particles.append([
                float(random.randint(0, W - 1)),
                float(random.randint(-H, 0)),
                random.uniform(-0.35, 0.35),
                random.uniform(0.2, 0.55),
            ])

# ── Lightning helpers ─────────────────────────────────────────────────────────
def make_bolt():
    global bolt_path
    bolt_path = []
    x = random.randint(W // 5, 4 * W // 5)
    y = 0
    while y < TEMP_Y - 2:
        bolt_path.append((x, y))
        y += 1
        if y % 3 == 0:
            x += random.choice([-2, -1, 1, 2])
            x  = max(2, min(W - 3, x))

# ── Weather API ───────────────────────────────────────────────────────────────
def geocode(city):
    url = ("https://geocoding-api.open-meteo.com/v1/search"
           "?name=" + city.replace(" ", "+") + "&count=1&language=en&format=json")
    resp = requests.get(url)
    data = json.loads(resp.text)
    resp.close()
    r = data["results"][0]
    return r["latitude"], r["longitude"], r["name"]

def fetch_weather():
    global weather_code, temperature, condition, status_msg, utc_offset
    global server_epoch, server_mono
    lat = cfg.get("lat", 0.0)
    lon = cfg.get("lon", 0.0)
    if not lat and not lon:
        status_msg = "Set a city"
        return
    try:
        url = ("https://api.open-meteo.com/v1/forecast"
               "?latitude=" + str(lat) +
               "&longitude=" + str(lon) +
               "&current=temperature_2m,weather_code"
               "&daily=sunrise,sunset"
               "&temperature_unit=celsius"
               "&timezone=auto")
        resp = requests.get(url)
        data = json.loads(resp.text)
        resp.close()
        cur          = data["current"]
        temperature  = cur["temperature_2m"]
        new_code     = cur["weather_code"]
        weather_code = new_code
        utc_offset   = data.get("utc_offset_seconds", 0)
        # Parse server local time from API (e.g. "2026-04-05T15:42")
        try:
            t_str = cur["time"]  # "YYYY-MM-DDTHH:MM"
            parts = t_str.split("T")
            ymd = parts[0].split("-")
            hm = parts[1].split(":")
            st = time.struct_time((int(ymd[0]), int(ymd[1]), int(ymd[2]),
                                   int(hm[0]), int(hm[1]), 0, -1, -1, -1))
            server_epoch = time.mktime(st)
            server_mono  = time.monotonic()
        except Exception:
            pass
        # Parse sunrise/sunset
        try:
            daily = data["daily"]
            for key, target in (("sunrise", "sunrise_epoch"), ("sunset", "sunset_epoch")):
                ts = daily[key][0]  # e.g. "2026-04-05T06:23"
                p2 = ts.split("T")
                ymd2 = p2[0].split("-")
                hm2 = p2[1].split(":")
                st2 = time.struct_time((int(ymd2[0]), int(ymd2[1]), int(ymd2[2]),
                                        int(hm2[0]), int(hm2[1]), 0, -1, -1, -1))
                globals()[target] = time.mktime(st2)
        except Exception:
            pass
        new_cond     = wmo_to_cond(new_code)
        if new_cond != condition:
            condition = new_cond
            init_scene(condition)
        status_msg = ""
        print("Weather:", temperature, "C, code:", weather_code, "->", condition)
    except Exception as e:
        status_msg = str(e)[:40]
        print("Weather fetch error:", e)

# ── Web routes ────────────────────────────────────────────────────────────────
@ampule.route("/exit", method="GET")
def wx_exit(request):
    load_settings.app_running = False
    return (200, {}, """<meta http-equiv="refresh" content="0; url=../" />""")

@ampule.route("/", method="GET")
def wx_home(request):
    return (200, {}, html)

@ampule.route("/debug", method="GET")
def wx_debug(request):
    return (200, {}, _DEBUG_HTML)

@ampule.route("/debug", method="POST")
def wx_debug_post(request):
    global condition, temperature, weather_code, sunrise_epoch, sunset_epoch
    global server_epoch, server_mono
    params = request.params
    mode = params.get("mode", "")
    if mode == "beach":
        condition = "clear"
        temperature = 28.0
        weather_code = 0
        # Force daytime
        server_epoch = time.mktime(time.localtime())
        server_mono  = time.monotonic()
        sunrise_epoch = server_epoch - 3600
        sunset_epoch  = server_epoch + 3600
        init_scene(condition)
    elif mode == "winter":
        condition = "snow"
        temperature = -5.0
        weather_code = 73
        init_scene(condition)
    elif mode == "clear_day":
        condition = "clear"
        temperature = 18.0
        weather_code = 0
        server_epoch = time.mktime(time.localtime())
        server_mono  = time.monotonic()
        sunrise_epoch = server_epoch - 3600
        sunset_epoch  = server_epoch + 3600
        init_scene(condition)
    elif mode == "clear_night":
        condition = "clear"
        temperature = 12.0
        weather_code = 0
        server_epoch = time.mktime(time.localtime())
        server_mono  = time.monotonic()
        sunrise_epoch = server_epoch + 3600
        sunset_epoch  = server_epoch - 3600
        init_scene(condition)
    elif mode == "partly_cloudy":
        condition = "partly_cloudy"
        temperature = 15.0
        weather_code = 2
        init_scene(condition)
    elif mode == "cloudy":
        condition = "cloudy"
        temperature = 10.0
        weather_code = 3
        init_scene(condition)
    elif mode == "rain":
        condition = "rain"
        temperature = 8.0
        weather_code = 63
        init_scene(condition)
    elif mode == "storm":
        condition = "storm"
        temperature = 6.0
        weather_code = 95
        init_scene(condition)
    elif mode == "fog":
        condition = "fog"
        temperature = 4.0
        weather_code = 45
        init_scene(condition)
    elif mode == "snow":
        condition = "snow"
        temperature = 1.0
        weather_code = 73
        init_scene(condition)
    elif mode == "drizzle":
        condition = "drizzle"
        temperature = 9.0
        weather_code = 53
        init_scene(condition)
    return (200, {}, json.dumps({"ok": True, "mode": mode}))

@ampule.route("/weather", method="GET")
def wx_data(request):
    desc = _WMO_DESC.get(weather_code, "No data") if weather_code >= 0 else "No data"
    return (200, {}, json.dumps({
        "temp": temperature,
        "desc": desc,
        "city": cfg.get("city", ""),
        "unit": cfg.get("unit", "C"),
        "code": weather_code,
    }))

@ampule.route("/settings", method="GET")
def wx_settings(request):
    return (200, {}, json.dumps(cfg))

@ampule.route("/", method="POST")
def wx_post(request):
    global last_fetch
    params = request.params
    if "city" in params:
        city = url_decoder(params["city"])
        try:
            lat, lon, name = geocode(city)
            cfg["city"] = name
            cfg["lat"]  = lat
            cfg["lon"]  = lon
            fetch_weather()
            last_fetch = time.monotonic()
            return (200, {}, json.dumps({"ok": True, "city": name}))
        except Exception as e:
            print("Geocode error:", e)
            return (200, {}, json.dumps({"error": "City not found"}))
    if "unit" in params:
        cfg["unit"] = params["unit"]
    if "interval" in params:
        try:
            cfg["interval"] = int(params["interval"])
        except Exception:
            pass
    if "clock" in params:
        try:
            cfg["clock"] = int(params["clock"])
        except Exception:
            pass
    if "clockmode" in params:
        v = params["clockmode"]
        if v in ("12", "24"):
            cfg["clockmode"] = v
    if "refresh" in params:
        fetch_weather()
        last_fetch = time.monotonic()
    if "save" in params:
        try:
            with open("weathersettings.txt", "w") as f:
                f.write(json.dumps(cfg))
        except Exception:
            pass
    return (200, {}, json.dumps({"ok": True}))

# ── Startup ───────────────────────────────────────────────────────────────────
clearscreen(lines=True)
window.fill(0)
display.refresh()

init_scene(condition)

if cfg.get("lat") and cfg.get("lon"):
    if cfg.get("city"):
        pprint(cfg["city"], line=-1, color="white")
        refresh()
    fetch_weather()
else:
    pprint("Set city", line=2)

last_fetch = time.monotonic()

# ── Main loop ─────────────────────────────────────────────────────────────────
while load_settings.app_running:

    # Periodic weather refresh
    if time.monotonic() - last_fetch >= cfg.get("interval", 300):
        fetch_weather()
        last_fetch = time.monotonic()

    # ── Sky background ────────────────────────────────────────────────────────
    _skyfn = _sky_solid
    if condition == "clear":
        _skyfn(6)
    elif condition == "partly_cloudy":
        _skyfn(12)
    elif condition == "cloudy":
        _skyfn(12)
    elif condition == "fog":
        _skyfn(10)
    elif condition in ("drizzle", "rain"):
        _skyfn(3)
    elif condition == "snow":
        _skyfn(12)
    elif condition == "storm":
        _skyfn(13)
        # Lightning: trigger and flash
        if frame >= next_lightning:
            lightning_age  = 0
            next_lightning = frame + random.randint(60, 140)
            make_bolt()
        if lightning_age < 3:
            palette[4] = (130, 130, 60)   # lightning yellow for flash
            # Flash only along the bolt path area, not full screen
            for bx, by in bolt_path:
                for dx in range(-3, 4):
                    _sp(bx + dx, by, 4)
        lightning_age += 1
    else:
        window.fill(0)

    # ── Sun / Moon (drawn before clouds so clouds can pass in front) ─────────
    if condition in ("clear", "partly_cloudy"):
        if _is_night():
            draw_moon(frame)
        else:
            draw_sun(frame)

    # ── Clouds ────────────────────────────────────────────────────────────────
    if condition != "clear":
        for cl in clouds:
            cl[0] -= 0.07
            if cl[0] + cl[2] < -5:
                cl[0] = float(W + 3)
            draw_cloud(int(cl[0]), int(cl[1]), cl[2], cl[3])

    # ── Birds (drawn on top of clouds) ───────────────────────────────────────
    if condition in ("clear", "partly_cloudy"):
        for b in birds:
            b[0] += b[3]
            b[2] += 0.12
            if b[0] > W + 5:
                b[0] = -5.0
                b[1] = float(random.randint(3, max(4, H // 2 - 8)))
            draw_bird(int(b[0]), int(b[1]), b[2])

    # ── Beach scene (clear + hot + daytime) ──────────────────────────────────
    if _is_beach():
        draw_beach(frame)

    # ── Winter scene (snow + freezing) ───────────────────────────────────────
    if _is_winter():
        draw_winter(frame)

    # ── Rain ──────────────────────────────────────────────────────────────────
    if condition in ("rain", "drizzle", "storm"):
        palette[15] = (40, 60, 100)   # rain drop blue-white
        new_p = []
        for p in particles:
            p[0] += p[2]
            p[1] += p[3]
            yi = int(p[1])
            xi = int(p[0])
            if yi < TEMP_Y:
                _sp(xi,     yi,     15)
                _sp(xi - 1, yi - 1, 15)   # angled streak
                new_p.append(p)
            else:
                # particle reached/passed temp-text row – respawn at top
                new_p.append([float(random.randint(0, W - 1)), -1.0, p[2], p[3]])
        particles = new_p

    # ── Snow ──────────────────────────────────────────────────────────────────
    elif condition == "snow":
        palette[15] = (90, 95, 110)   # snowflake pale blue-white
        new_p = []
        for p in particles:
            # gentle side-to-side drift
            p[0] = (p[0] + p[2] + math.sin(frame * 0.04 + p[0] * 0.15) * 0.08) % W
            p[1] += p[3]
            xi = int(p[0])
            yi = int(p[1])
            if yi < TEMP_Y:
                _sp(xi, yi, 15)
                new_p.append([p[0], p[1], p[2], p[3]])
            else:
                # snowflake reached bottom – respawn at top
                new_p.append([float(random.randint(0, W - 1)), -1.0, p[2], p[3]])
        particles = new_p

    # ── Lightning bolt (drawn on top of rain, after flash fades) ─────────────
    if condition == "storm":
        palette[4] = (130, 130, 60)   # lightning yellow
        if 3 <= lightning_age < 12:
            for bx, by in bolt_path:
                _sp(bx,     by, 4)
                _sp(bx + 1, by, 4)

    # ── Bottom bar: city (left) · clock (centre) · temp (right) ────────────────

    _city = cfg.get("city", "")
    if _city:
        _maxc = W // 5
        draw_text(_city[:_maxc].lower(), 1, TEMP_Y, 5)

    if temperature is not None:
        t = temperature
        if cfg.get("unit") == "F":
            t = t * 9.0 / 5.0 + 32.0
        sign = "-" if t < 0 else ""
        ts = sign + str(abs(int(t))) + ("f" if cfg.get("unit") == "F" else "c") + "°"
        tw = text_width(ts)
        draw_text(ts, W - tw - 1, TEMP_Y, 5)
    elif status_msg:
        draw_text(status_msg[: W // 4], 2, TEMP_Y, 5)

    if cfg.get("clock") and server_epoch:
        now_epoch = server_epoch + int(time.monotonic() - server_mono)
        lt = time.localtime(now_epoch)
        hr = lt.tm_hour
        if cfg.get("clockmode") == "12":
            suffix = "a" if hr < 12 else "p"
            hr = hr % 12
            if hr == 0:
                hr = 12
            hh = str(hr)
            mm = "%02d" % lt.tm_min
            cts = hh + ":" + mm + suffix
        else:
            hh = str(hr)
            mm = "%02d" % lt.tm_min
            cts = hh + ":" + mm
        cw = text_width(cts)
        draw_text(cts, (W - cw) // 2, TEMP_Y, 5)

    frame += 1
    refresh()
    ampule.listen(socket)

    b = check_if_button_pressed()
    if b == 2:
        sys.exit()
    elif b == 1:
        # Short press: force weather refresh
        fetch_weather()
        last_fetch = time.monotonic()

clearscreen()

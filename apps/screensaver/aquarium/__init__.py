from __main__ import *
import sys, time, random, math
import load_screen
from check_button import check_if_button_pressed
from load_screen import *
microcontroller.cpu.frequency = 240000000

W = display_width()
H = display_height()

# --- Settings ---
try:
    with open("aquarium/aquasettings.txt") as f:
        cfg = json.loads(f.read())
except:
    cfg = {"max_fish": 5, "fish_types": "clown,tang,blue,pink",
           "bubbles": True, "max_bubbles": 6, "caustics": True,
           "bubble_rate": 2, "fish_rate": 2}

def save_cfg():
    with open("aquarium/aquasettings.txt", "w") as f:
        f.write(json.dumps(cfg))

# Settings fragment composed into the screensaver's one settings page (see code.py)
SETTINGS_FRAGMENT = """<div class="card">
<div class="section-title">Fish</div>
<label>Fish Count</label>
<div class="range-wrap">
<input type="range" id="maxFish" min="0" max="10" value="5" oninput="g('fishVal').textContent=this.value" onchange="send('max_fish='+this.value)">
<span class="range-val" id="fishVal">5</span>
</div>

<label>Fish Types</label>
<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:4px" id="fishTypes">
<label style="display:flex;align-items:center;gap:6px;background:var(--surface2);padding:6px 10px;border-radius:8px;font-size:.85rem;text-transform:none;letter-spacing:0;margin:0;cursor:pointer"><input type="checkbox" value="clown" onchange="updateTypes()" style="accent-color:var(--accent)"> Clownfish</label>
<label style="display:flex;align-items:center;gap:6px;background:var(--surface2);padding:6px 10px;border-radius:8px;font-size:.85rem;text-transform:none;letter-spacing:0;margin:0;cursor:pointer"><input type="checkbox" value="tang" onchange="updateTypes()" style="accent-color:var(--accent)"> Yellow Tang</label>
<label style="display:flex;align-items:center;gap:6px;background:var(--surface2);padding:6px 10px;border-radius:8px;font-size:.85rem;text-transform:none;letter-spacing:0;margin:0;cursor:pointer"><input type="checkbox" value="blue" onchange="updateTypes()" style="accent-color:var(--accent)"> Blue Fish</label>
<label style="display:flex;align-items:center;gap:6px;background:var(--surface2);padding:6px 10px;border-radius:8px;font-size:.85rem;text-transform:none;letter-spacing:0;margin:0;cursor:pointer"><input type="checkbox" value="pink" onchange="updateTypes()" style="accent-color:var(--accent)"> Pink Fish</label>
</div>

<label style="margin-top:14px">Spawn Rate</label>
<div class="seg" id="fishRate">
<button data-v="1" onclick="setRate('fishRate',1);send('fish_rate=1')">Slow</button>
<button data-v="2" onclick="setRate('fishRate',2);send('fish_rate=2')">Medium</button>
<button data-v="3" onclick="setRate('fishRate',3);send('fish_rate=3')">Fast</button>
</div>
</div>

<div class="card">
<div class="section-title">Bubbles</div>
<div class="toggle-item"><span>Enable Bubbles</span><label class="sw"><input type="checkbox" id="bubbles" onchange="send('bubbles='+this.checked)"><span class="sl"></span></label></div>
<label>Max Bubbles</label>
<div class="range-wrap">
<input type="range" id="maxBub" min="0" max="12" value="6" oninput="g('bubVal').textContent=this.value" onchange="send('max_bubbles='+this.value)">
<span class="range-val" id="bubVal">6</span>
</div>
<label style="margin-top:14px">Bubble Rate</label>
<div class="seg" id="bubRate">
<button data-v="1" onclick="setRate('bubRate',1);send('bubble_rate=1')">Slow</button>
<button data-v="2" onclick="setRate('bubRate',2);send('bubble_rate=2')">Medium</button>
<button data-v="3" onclick="setRate('bubRate',3);send('bubble_rate=3')">Fast</button>
</div>
</div>

<div class="card">
<div class="section-title">Lighting</div>
<div class="toggle-item"><span>Caustic Light Effect</span><label class="sw"><input type="checkbox" id="caustics" onchange="send('caustics='+this.checked)"><span class="sl"></span></label></div>
</div>

<button class="btn btn-full" id="saveBtn" onclick="sv()">&#128190; Save Settings</button>

<script>
function g(id){return document.getElementById(id)}
function send(p){fetch("/settings?"+p,{method:"POST"}).then(r=>r.json()).catch(()=>{})}
function setRate(id,v){document.querySelectorAll("#"+id+" button").forEach(function(b){b.classList.toggle("on",parseInt(b.dataset.v)===v)})}
function updateTypes(){var t=[];document.querySelectorAll("#fishTypes input:checked").forEach(function(c){t.push(c.value)});if(t.length==0)return;send("fish_types="+t.join(","))}
function sv(){var b=g("saveBtn");b.textContent="Saved!";send("save=1");setTimeout(function(){b.innerHTML="&#128190; Save Settings"},1500)}
function load(){
 fetch("/settings/json").then(r=>r.json()).then(function(d){
  g("maxFish").value=d.max_fish||5;g("fishVal").textContent=d.max_fish||5;
  g("maxBub").value=d.max_bubbles||6;g("bubVal").textContent=d.max_bubbles||6;
  g("bubbles").checked=d.bubbles!==false;
  g("caustics").checked=d.caustics!==false;
  var ft=(d.fish_types||"clown,tang,blue,pink").split(",");
  document.querySelectorAll("#fishTypes input").forEach(function(cb){cb.checked=ft.indexOf(cb.value)>=0});
  setRate("fishRate",d.fish_rate||2);
  setRate("bubRate",d.bubble_rate||2);
 });
}
load();
</script>"""

# --- Web routes ---
@ampule.route("/settings/json", method="GET")
def get_settings(request):
    return (200, {}, json.dumps(cfg))

@ampule.route("/settings", method="POST")
def aqua_post(request):
    global cfg
    changed = False
    if "max_fish" in request.params:
        v = int(request.params["max_fish"])
        if 0 <= v <= 10:
            cfg["max_fish"] = v; changed = True
    if "fish_types" in request.params:
        cfg["fish_types"] = request.params["fish_types"]; changed = True
    if "bubbles" in request.params:
        cfg["bubbles"] = request.params["bubbles"] == "true"; changed = True
    if "max_bubbles" in request.params:
        v = int(request.params["max_bubbles"])
        if 0 <= v <= 12:
            cfg["max_bubbles"] = v; changed = True
    if "caustics" in request.params:
        cfg["caustics"] = request.params["caustics"] == "true"; changed = True
    if "bubble_rate" in request.params:
        v = int(request.params["bubble_rate"])
        if 1 <= v <= 3:
            cfg["bubble_rate"] = v; changed = True
    if "fish_rate" in request.params:
        v = int(request.params["fish_rate"])
        if 1 <= v <= 3:
            cfg["fish_rate"] = v; changed = True
    if "save" in request.params:
        save_cfg()
    return (200, {}, json.dumps(cfg))

# Palette
palette[0] = (0, 8, 28)         # deep water
palette[1] = (2, 16, 45)        # water highlight
palette[2] = (8, 30, 60)        # lighter water / caustic
palette[3] = (200, 200, 220)    # bubble
palette[4] = (255, 100, 20)     # clownfish orange
palette[5] = (255, 255, 255)    # clownfish white stripe / bubble shine
palette[6] = (0, 180, 80)       # seaweed green
palette[7] = (0, 120, 50)       # seaweed dark
palette[8] = (255, 220, 40)     # yellow tang
palette[9] = (80, 80, 220)      # blue fish
palette[10] = (220, 60, 120)    # pink fish
palette[11] = (140, 90, 50)     # sand
palette[12] = (180, 140, 80)    # sand highlight
palette[13] = (100, 60, 35)     # rock / chest dark
palette[14] = (40, 150, 40)     # plant bright
palette[15] = (200, 80, 80)     # red coral
# Note: idx 8 (yellow) doubles as chest gold & food pellet color

SAND_H = 5  # max sand height

# --- Sand bank terrain (precomputed per column) ---
# Gentle sine curves for uneven bottom
sand_top = [0] * W
for _sx in range(W):
    # Two overlapping sine waves for natural look
    h = 2.5 + math.sin(_sx * 0.12) * 1.2 + math.sin(_sx * 0.28 + 1.5) * 0.8
    sand_top[_sx] = H - int(h)

# --- Fish ---
# Each fish: shape drawn as pixels relative to body center
# Facing right; flip for left
# Small fish: 5px wide, 3px tall
# body_col = main color, stripe_col = accent
# Fish type table: name -> (body_col, stripe_col, size)
FISH_KINDS = {
    "clown": (4, 5, 1),
    "tang":  (8, 5, 1),
    "blue":  (9, 8, 0),
    "pink":  (10, 5, 0),
}

class Fish:
    def __init__(self):
        self.facing = random.choice([-1, 1])
        self.x = float(3 if self.facing == 1 else W - 4)
        self.y = float(random.randint(2, min(sand_top) - 4))
        self.speed = random.uniform(0.3, 0.8)
        self.phase = random.uniform(0, 6.28)
        self.bob_speed = random.uniform(0.05, 0.1)
        self.bob_amp = random.uniform(0.3, 0.8)
        self.paused = False
        self.target = None  # food target (x, y)
        # Pick from allowed types
        allowed = [k.strip() for k in cfg.get("fish_types", "clown,tang,blue,pink").split(",") if k.strip() in FISH_KINDS]
        if not allowed:
            allowed = list(FISH_KINDS.keys())
        kind = random.choice(allowed)
        self.body, self.stripe, self.sz = FISH_KINDS[kind]

    def update(self):
        # Check for food to chase
        if food_list and self.target is None:
            # Pick nearest food
            best_d = 9999
            best_f = None
            for fd in food_list:
                d = abs(fd.x - self.x) + abs(fd.y - self.y)
                if d < best_d:
                    best_d = d
                    best_f = fd
            if best_f and best_d < 60:
                self.target = best_f

        if self.target is not None:
            # Swim toward food
            self.paused = False
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            if dx > 1: self.facing = 1
            elif dx < -1: self.facing = -1
            self.x += self.speed * 1.5 * (1 if dx > 0 else -1)
            if abs(dy) > 0.5:
                self.y += 0.4 * (1 if dy > 0 else -1)
            # Eat if close
            if abs(dx) < 3 and abs(dy) < 3:
                if self.target in food_list:
                    food_list.remove(self.target)
                self.target = None
        else:
            # Normal behavior
            r = random.random()
            if r < 0.005:
                self.facing = -self.facing
            elif r < 0.012:
                self.paused = not self.paused

            if not self.paused:
                self.x += self.speed * self.facing
            self.phase += self.bob_speed
            self.y += math.sin(self.phase) * self.bob_amp * 0.3

        # Vertical bounds (respect sand terrain)
        if self.y < 1: self.y = 1.0
        ix = max(0, min(int(self.x), W - 1))
        max_y = sand_top[ix] - 3
        if self.y > max_y: self.y = float(max_y)
        # Turn around at screen edges
        margin = 3 if self.sz == 0 else 4
        if self.x >= W - margin:
            self.x = float(W - margin)
            self.facing = -1
        elif self.x <= margin:
            self.x = float(margin)
            self.facing = 1

    def alive(self):
        return True

    def draw(self):
        ix = int(self.x)
        iy = int(self.y)
        f = self.facing
        if self.sz == 1:
            # Bigger fish (5w x 3h)
            # Row 0:       .B.
            # Row 1: TB.BSB.BT
            # Row 2:       .B.
            # (T=tail, B=body, S=stripe)
            _sp(ix, iy - 1, self.body)
            _sp(ix - 1 * f, iy, self.body)
            _sp(ix, iy, self.body)
            _sp(ix + 1 * f, iy, self.stripe)
            _sp(ix + 2 * f, iy, self.body)
            _sp(ix, iy + 1, self.body)
            # Tail
            _sp(ix - 2 * f, iy - 1, self.body)
            _sp(ix - 2 * f, iy, self.body)
            _sp(ix - 2 * f, iy + 1, self.body)
            # Eye
            _sp(ix + 2 * f, iy - 1, 5)
        else:
            # Small fish (3w x 3h)
            _sp(ix, iy, self.body)
            _sp(ix + 1 * f, iy, self.stripe)
            _sp(ix - 1 * f, iy - 1, self.body)
            _sp(ix - 1 * f, iy, self.body)
            _sp(ix - 1 * f, iy + 1, self.body)
            _sp(ix + 1 * f, iy - 1, 5)

def _sp(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        window[x, y] = c

# --- Bubbles ---
class Bubble:
    def __init__(self):
        sx = random.randint(3, W - 3)
        self.x = float(sx)
        self.y = float(sand_top[sx] - 1)
        # Size: 0=tiny, 1=small, 2=medium — bigger ones rise slower
        r = random.random()
        if r < 0.55:
            self.size = 0
        elif r < 0.88:
            self.size = 1
        else:
            self.size = 2
        if self.size == 0:
            self.vy = random.uniform(-0.45, -0.25)
        elif self.size == 1:
            self.vy = random.uniform(-0.3, -0.15)
        else:
            self.vy = random.uniform(-0.2, -0.1)
        self.wobble = random.uniform(0.03, 0.08)
        self.phase = random.uniform(0, 6.28)

    def update(self):
        self.y += self.vy
        self.phase += self.wobble
        self.x += math.sin(self.phase) * 0.2

    def alive(self):
        return self.y > -2

    def draw(self):
        ix = int(self.x)
        iy = int(self.y)
        if self.size == 0:
            # Tiny: single pixel
            _sp(ix, iy, 3)
        elif self.size == 1:
            # Small: 2px with shine
            _sp(ix, iy, 3)
            _sp(ix, iy - 1, 5)
        else:
            # Medium: 2x2 with shine
            _sp(ix, iy, 3)
            _sp(ix + 1, iy, 3)
            _sp(ix, iy - 1, 3)
            _sp(ix + 1, iy - 1, 5)

# --- Seaweed ---
class Seaweed:
    def __init__(self, x):
        self.x = x
        self.h = random.randint(4, 9)
        self.phase = random.uniform(0, 6.28)
        self.speed = random.uniform(0.02, 0.05)
        self.col = random.choice([6, 7, 14])

    def draw(self, frame):
        self.phase += self.speed
        base_y = sand_top[max(0, min(self.x, W - 1))] - 1
        for i in range(self.h):
            py = base_y - i
            # Sway increases with height
            sway = math.sin(self.phase + i * 0.5) * (i * 0.25)
            px = int(self.x + sway)
            c = self.col if i % 3 != 0 else 6
            _sp(px, py, c)

# --- Food ---
class Food:
    def __init__(self):
        self.x = float(random.randint(5, W - 5))
        self.y = 0.0
        self.vy = random.uniform(0.15, 0.3)
        self.wobble = random.uniform(0.03, 0.06)
        self.phase = random.uniform(0, 6.28)

    def update(self):
        self.y += self.vy
        self.phase += self.wobble
        self.x += math.sin(self.phase) * 0.15
        # Stop at sand
        ix = max(0, min(int(self.x), W - 1))
        if self.y >= sand_top[ix] - 1:
            self.y = float(sand_top[ix] - 1)

    def alive(self):
        # Disappear after settling on sand for a while
        ix = max(0, min(int(self.x), W - 1))
        return self.y < sand_top[ix] - 0.5

    def draw(self):
        _sp(int(self.x), int(self.y), 8)

food_list = []

# --- Treasure chest ---
# Place on a high point of sand
_chest_x = W // 3 + random.randint(-5, 5)
_chest_base = sand_top[max(0, min(_chest_x, W - 1))]

def draw_chest():
    cx = _chest_x
    by = _chest_base
    # Chest body (6w x 6h): dark brown with gold latch and lid
    # Bottom row (base)
    for i in range(6):
        _sp(cx + i, by - 1, 13)
    # Row 2 - body with gold trim
    _sp(cx, by - 2, 13); _sp(cx + 1, by - 2, 11); _sp(cx + 2, by - 2, 8); _sp(cx + 3, by - 2, 8); _sp(cx + 4, by - 2, 11); _sp(cx + 5, by - 2, 13)
    # Row 3 - body with gold latch
    _sp(cx, by - 3, 13); _sp(cx + 1, by - 3, 11); _sp(cx + 2, by - 3, 8); _sp(cx + 3, by - 3, 8); _sp(cx + 4, by - 3, 11); _sp(cx + 5, by - 3, 13)
    # Row 4 - lid band
    for i in range(6):
        _sp(cx + i, by - 4, 13)
    # Row 5 - lid top
    _sp(cx, by - 5, 13); _sp(cx + 1, by - 5, 13); _sp(cx + 2, by - 5, 12); _sp(cx + 3, by - 5, 12); _sp(cx + 4, by - 5, 13); _sp(cx + 5, by - 5, 13)
    # Row 6 - lid crown
    _sp(cx + 1, by - 6, 13); _sp(cx + 2, by - 6, 13); _sp(cx + 3, by - 6, 13); _sp(cx + 4, by - 6, 13)

# --- Setup scene ---
fish_list = []
fish_timer = 0.0
bubble_list = []
bubble_timer = 0.0

# Seaweed patches
weeds = []
for _ in range(5):
    wx = random.randint(3, W - 3)
    weeds.append(Seaweed(wx))

# Rocks on sand (sit on terrain)
rocks = []
for _ in range(4):
    rx = random.randint(2, W - 3)
    rocks.append((rx, sand_top[rx] - 1, 13))

# Coral spots (sit on terrain)
corals = []
for _ in range(3):
    ccx = random.randint(5, W - 5)
    corals.append(ccx)

frame = 0

while load_settings.app_running:
    window.fill(0)
    now = time.monotonic()

    # Caustic light shimmer on water
    if cfg.get("caustics", True):
        for px in range(W):
            v = int(math.sin(frame * 0.08 + px * 0.4) * 2)
            if v > 0:
                _sp(px, v, 2)
                _sp(px, v + 1, 1)

    # Sand bank terrain
    for px in range(W):
        st = sand_top[px]
        for py in range(st, H):
            window[px, py] = 11 if py == st else 12

    # Rocks
    for rx, ry, rc in rocks:
        _sp(rx, ry, rc)
        _sp(rx + 1, ry, rc)
        _sp(rx, ry - 1, rc)

    # Coral
    for ccx in corals:
        cy = sand_top[max(0, min(ccx, W - 1))] - 1
        _sp(ccx, cy, 15)
        _sp(ccx + 1, cy, 15)
        _sp(ccx, cy - 1, 15)
        _sp(ccx - 1, cy - 1, 15)

    # Treasure chest
    draw_chest()

    # Seaweed
    for w in weeds:
        w.draw(frame)

    # Spawn fish — rate: 1=slow, 2=medium, 3=fast
    _fr = cfg.get("fish_rate", 2)
    _f_delay = (5.5 - _fr * 1.5, 9.0 - _fr * 2.0)
    _mf = cfg.get("max_fish", 5)
    if now > fish_timer and len(fish_list) < _mf and _mf > 0:
        fish_list.append(Fish())
        fish_timer = now + random.uniform(_f_delay[0], _f_delay[1])

    alive = []
    for f in fish_list:
        f.update()
        f.draw()
        if f.alive():
            alive.append(f)
    fish_list = alive

    # Spawn bubbles
    _mb = cfg.get("max_bubbles", 6)
    _br = cfg.get("bubble_rate", 2)
    _b_delay = (3.5 - _br * 1.0, 5.5 - _br * 1.2)
    if cfg.get("bubbles", True) and now > bubble_timer and len(bubble_list) < _mb and _mb > 0:
        bubble_list.append(Bubble())
        bubble_timer = now + random.uniform(_b_delay[0], _b_delay[1])

    balive = []
    for bu in bubble_list:
        bu.update()
        bu.draw()
        if bu.alive():
            balive.append(bu)
    bubble_list = balive

    # Draw and update food
    falive = []
    for fd in food_list:
        fd.update()
        fd.draw()
        if fd.alive():
            falive.append(fd)
    food_list = falive

    frame += 1
    refresh()
    ampule.listen(socket)

    b = check_if_button_pressed()
    if b == 1:
        # Short press: drop food
        for _ in range(random.randint(2, 4)):
            food_list.append(Food())
    elif b == 2:
        sys.exit()

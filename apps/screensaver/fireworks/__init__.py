from __main__ import *
import sys, time, random
import load_screen
from check_button import check_if_button_pressed
from load_screen import *
microcontroller.cpu.frequency = 240000000
import math, random

# Tuneable settings
fw_settings = {
    "particles": 75,
    "max_active": 3,
    "gravity": 10,
    "speed": 20,
    "lifetime": 30,
    "delay": 10,
}
try:
    with open("fireworks/fwsettings.txt") as f:
        fw_settings.update(json.loads(f.read()))
except: pass

# Settings fragment composed into the screensaver's one settings page (see code.py)
SETTINGS_FRAGMENT = """<div class="card">
<div class="section-title">Fireworks</div>
<label>Particles per burst</label>
<div class="range-wrap"><input type="range" id="fw_particles" min="20" max="150" step="5" oninput="g('v_particles').textContent=this.value" onchange="fwSet('particles',this.value)"><span class="range-val" id="v_particles">75</span></div>
<label>Max simultaneous</label>
<div class="range-wrap"><input type="range" id="fw_max_active" min="1" max="8" oninput="g('v_max_active').textContent=this.value" onchange="fwSet('max_active',this.value)"><span class="range-val" id="v_max_active">3</span></div>
<label>Gravity</label>
<div class="range-wrap"><input type="range" id="fw_gravity" min="0" max="30" oninput="g('v_gravity').textContent=this.value" onchange="fwSet('gravity',this.value)"><span class="range-val" id="v_gravity">10</span></div>
<label>Speed</label>
<div class="range-wrap"><input type="range" id="fw_speed" min="5" max="50" oninput="g('v_speed').textContent=this.value" onchange="fwSet('speed',this.value)"><span class="range-val" id="v_speed">20</span></div>
<label>Lifetime</label>
<div class="range-wrap"><input type="range" id="fw_lifetime" min="10" max="80" step="5" oninput="g('v_lifetime').textContent=this.value" onchange="fwSet('lifetime',this.value)"><span class="range-val" id="v_lifetime">30</span></div>
<label>Launch delay</label>
<div class="range-wrap"><input type="range" id="fw_delay" min="1" max="30" oninput="g('v_delay').textContent=this.value" onchange="fwSet('delay',this.value)"><span class="range-val" id="v_delay">10</span></div>
</div>
<button class="btn btn-full" id="fwSaveBtn" onclick="fwSave()">&#128190; Save Settings</button>
<script>
function g(id){return document.getElementById(id)}
function fwSet(k,v){fetch('/set?k='+k+'&v='+v)}
function fwSave(){var b=g('fwSaveBtn');b.textContent='Saved!';fetch('/save');setTimeout(function(){b.innerHTML='&#128190; Save Settings'},1500)}
(function(){fetch('/settings/json').then(function(r){return r.json()}).then(function(d){
['particles','max_active','gravity','speed','lifetime','delay'].forEach(function(k){
if(d[k]!==undefined){g('fw_'+k).value=d[k];g('v_'+k).textContent=d[k]}})})})();
</script>"""

@ampule.route("/settings/json", method="GET")
def fireworks_values(request):
    return (200, {}, json.dumps(fw_settings))


@ampule.route("/set", method="GET")
def set_param(request):
    if request.params and "k" in request.params and "v" in request.params:
        k = request.params["k"]
        if k in fw_settings:
            fw_settings[k] = int(request.params["v"])
    return (200, {}, "ok")

@ampule.route("/save", method="GET")
def save_settings(request):
    try:
        with open("fireworks/fwsettings.txt", "w") as f:
            f.write(json.dumps(fw_settings))
    except: pass
    return (200, {}, "ok")

width = display_width()
height = display_height()

def create_firework(x, y):
    particles = []
    num_particles = fw_settings["particles"]
    colors = [random.randint(1, 15) for _ in range(3)]
    spd = fw_settings["speed"] / 10.0
    lt = fw_settings["lifetime"]
    for _ in range(num_particles):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.3, spd)
        vx = speed * math.cos(angle)
        vy = speed * math.sin(angle)
        lifetime = random.randint(lt // 2, lt)
        color = random.choice(colors)
        particles.append({
            "x": x,
            "y": y,
            "vx": vx,
            "vy": vy,
            "lifetime": lifetime,
            "color": color
        })
    return particles

fireworks = []
last_firework_time = 0

while load_settings.app_running:
    current_time = time.monotonic()

    window.fill(0)

    # Create new fireworks randomly
    fw_delay = fw_settings["delay"] / 10.0
    if current_time - last_firework_time > fw_delay and len(fireworks) < fw_settings["max_active"]:
        x = random.randint(10, width - 10)
        y = random.randint(height // 4, height // 2)
        fireworks.append(create_firework(x, y))
        last_firework_time = current_time

    # Update and draw particles
    grav = fw_settings["gravity"] / 100.0
    new_fireworks = []
    for firework in fireworks:
        active_particles = []
        for particle in firework:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["vy"] += grav

            particle["lifetime"] -= 1
            if particle["lifetime"] > 0 and 0 <= int(particle["x"]) < width and 0 <= int(particle["y"]) < height:
                pset(int(particle["x"]), int(particle["y"]), particle["color"])
                active_particles.append(particle)

        if active_particles:
            new_fireworks.append(active_particles)

    fireworks = new_fireworks

    refresh()
    ampule.listen(socket)

    b = check_if_button_pressed()
    if b: sys.exit()

from __main__ import *
import digitalio, board
def time_button():
    return 1 - button.value

_btn_state = 0  # 0=IDLE, 1=WAIT_DEBOUNCE, 2=WAIT_LONG, 3=WAIT_RELEASE, 4=CONFIRM_RELEASE
_btn_time = 0
_release_time = 0
_long_threshold = 0.8  # seconds held before counted as long press
_noise_threshold = 0.03  # presses shorter than this are treated as noise

def check_if_button_pressed(strict=True):
    global _btn_state, _btn_time, _release_time
    now = time.monotonic()
    pressed = time_button()

    if _btn_state == 0:
        if pressed:
            _btn_time = now
            _btn_state = 1
        return 0

    if _btn_state == 1:  # noise filter on press
        if strict and now - _btn_time < _noise_threshold:
            return 0  # too short — wait
        if not pressed:
            _btn_state = 0  # gone within noise window — discard
            return 0
        _btn_state = 2  # held long enough to be real — proceed
        return 0

    if _btn_state == 2:  # waiting for long threshold
        if now - _btn_time >= _long_threshold:
            _btn_state = 3
            return 2
        if not pressed:
            # don't immediately fire - debounce the release too
            _release_time = now
            _btn_state = 4
        return 0

    if _btn_state == 3:  # wait for release after long press
        if not pressed:
            _btn_state = 0
        return 0

    if _btn_state == 4:  # confirm release (debounce)
        if pressed:
            _btn_state = 2  # bounce - still holding
            return 0
        if now - _release_time >= debounce_delay:
            _btn_state = 0
            return 1
        return 0

    return 0
    
    

button = digitalio.DigitalInOut(board.RX) # RX-pinnen för ena
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

gbutton = digitalio.DigitalInOut(board.TX) # TX-pinnena för andra
gbutton.direction = digitalio.Direction.INPUT
gbutton.pull = digitalio.Pull.DOWN

last_button_state = False

button_delay = 15000
debounce_delay = 0.2
short_button = 100
long_button = 20000
if settings["width"] == 192 or settings["height"] == 64:
    short_button = 1000
    long_button = 2000

from __main__ import *
init_display(bit_depth=5)
ampule.routes.clear()
# Needs bit_depth=5 for smoother map-mode gradients (vs. the shared default
# of 4); 6 overflows available RAM for the framebuffer at this resolution.
# This rebuilds the matrix/display, so it has to happen before code.py
# (imported below) touches display/window/palette. Restored back to 4 by
# main.py's initialize_app() when this app exits (also here, for clarity).

import code
init_display(bit_depth=4)
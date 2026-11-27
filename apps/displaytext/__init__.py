from __main__ import *
ampule.routes.clear()
# Needs bit_depth=5 for a much wider range of custom text colors (vs. the
# shared default of 4) -- this rebuilds the matrix/display, so it has to
# happen before code.py (imported below) touches display/window/palette.
# Restored back to 4 by main.py's initialize_app() when this app exits
# (also here, for clarity).
init_display(bit_depth=5)
try: import code
except: 
    print("Could not use bit_depth 5 - using 4")
    init_display(bit_depth=4)
    import code
init_display(bit_depth=4)
"""Path helper. RES = bundled read-only resources (scripts, recipes, fonts, tools); WORK = writable folder
(next to the .exe, or next to the scripts) where temporary files, reports and backups are created."""
import os, sys
if getattr(sys, 'frozen', False):
    RES = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    WORK = os.path.dirname(os.path.abspath(sys.executable))
else:
    RES = WORK = os.path.dirname(os.path.abspath(__file__))

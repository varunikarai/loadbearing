"""The hosted demo as a Vercel Python function: the same pages as `loadbearing serve --readonly`.

Free targets run on request; anything that would spend credits shows its recorded run.
/tmp is the only writable place on the host, so the recorded runs are copied there once
per instance and free runs are cached beside them.
"""

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
os.chdir(ROOT)  # relative target folders keep their labels on the index ("bench/cases")

from loadbearing.serve import Demo, wsgi_app  # noqa: E402

CACHE = Path("/tmp/loadbearing-runs")
if not CACHE.exists():
    shutil.copytree(ROOT / "demo" / "runs", CACHE)

# Targets run `python3 pipeline.py`; make that the interpreter this function itself runs on.
BIN = Path("/tmp/loadbearing-bin")
BIN.mkdir(exist_ok=True)
if not (BIN / "python3").exists():
    (BIN / "python3").symlink_to(sys.executable)
os.environ["PATH"] = f"{BIN}{os.pathsep}{os.environ.get('PATH', '')}"

app = wsgi_app(Demo(["examples", "bench/cases"], CACHE, "local", readonly=True))

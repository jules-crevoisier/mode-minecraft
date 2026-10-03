#!/usr/bin/env python3
"""Regenerate every generated resource, then validate. Run from anywhere:  python3 tools/generate_all.py"""
import os
import subprocess
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
STEPS = ["gen_structures.py", "gen_loot.py", "gen_quests.py", "gen_data.py", "gen_textures.py", "gen_gui.py", "gen_models.py", "gen_assets.py",
         "gen_java.py", "validate.py"]

for step in STEPS:
    print(f"== {step}")
    result = subprocess.run([sys.executable, os.path.join(TOOLS, step)] + sys.argv[1:] * (step in ("gen_structures.py", "gen_models.py")))
    if result.returncode != 0:
        sys.exit(result.returncode)

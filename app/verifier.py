import json
import os
import py_compile
from pathlib import Path

def verify(project):
    errors = []
    for base, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if d not in {".git","node_modules","__pycache__",".venv","venv"}]
        for fn in files:
            path = os.path.join(base, fn)
            ext = Path(fn).suffix.lower()
            if ext == ".py":
                try:
                    py_compile.compile(path, doraise=True)
                except Exception as e:
                    errors.append(f"Python compile error in {os.path.relpath(path, project)}: {e}")
            elif ext == ".json" and os.path.getsize(path) <= 2*1024*1024:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        json.load(f)
                except Exception as e:
                    errors.append(f"JSON error in {os.path.relpath(path, project)}: {e}")
    return errors

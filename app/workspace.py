import os
import re
import shutil
import zipfile
from pathlib import Path
from app.config import WORKSPACE_DIR, MAX_UPLOAD_MB

TEXT_EXTS = {
    ".py",".js",".ts",".tsx",".jsx",".java",".kt",".go",".rs",".c",".cpp",".h",".hpp",
    ".json",".yaml",".yml",".toml",".ini",".cfg",".txt",".md",".html",".css",".scss",
    ".sql",".sh",".bat",".ps1",".xml",".env.example"
}
MAX_FILE_BYTES = 512 * 1024
MAX_FILES = 3000

def user_root(tid):
    p = os.path.join(WORKSPACE_DIR, str(tid))
    os.makedirs(p, exist_ok=True)
    return p

def safe_member(name):
    name = name.replace("\\", "/").lstrip("/")
    parts = [p for p in name.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        return None
    if ":" in parts[0] if parts else False:
        return None
    return "/".join(parts)

def extract_zip(tid, zip_path):
    root = user_root(tid)
    project = os.path.join(root, "project")
    shutil.rmtree(project, ignore_errors=True)
    os.makedirs(project, exist_ok=True)
    total = 0
    with zipfile.ZipFile(zip_path) as z:
        infos = z.infolist()
        if len(infos) > MAX_FILES:
            raise ValueError("ZIP contains too many files.")
        for info in infos:
            safe = safe_member(info.filename)
            if not safe:
                raise ValueError("Unsafe ZIP path detected.")
            if info.is_dir():
                continue
            total += info.file_size
            if total > MAX_UPLOAD_MB * 1024 * 1024:
                raise ValueError("ZIP is too large.")
            out = os.path.join(project, safe)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with z.open(info) as src, open(out, "wb") as dst:
                shutil.copyfileobj(src, dst)
    return project

def project_context(project):
    rows = []
    for base, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if d not in {".git","node_modules","__pycache__",".venv","venv","dist","build"}]
        for fn in files:
            path = os.path.join(base, fn)
            rel = os.path.relpath(path, project).replace(os.sep, "/")
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            rows.append((rel, size))
    rows.sort()
    return rows

def read_text_files(project, limit=180000):
    chunks = []
    used = 0
    for rel, size in project_context(project):
        ext = Path(rel).suffix.lower()
        if ext not in TEXT_EXTS or size > MAX_FILE_BYTES:
            continue
        path = os.path.join(project, rel)
        try:
            text = open(path, "r", encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        block = f"\n--- FILE: {rel} ---\n{text}\n"
        if used + len(block) > limit:
            break
        chunks.append(block)
        used += len(block)
    return "".join(chunks)

def apply_changes(project, changes):
    applied = []
    for item in changes:
        rel = safe_member(str(item.get("path","")))
        content = item.get("content")
        if not rel or not isinstance(content, str):
            continue
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            continue
        out = os.path.join(project, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(content)
        applied.append(rel)
    return applied

def export_zip(tid):
    root = user_root(tid)
    project = os.path.join(root, "project")
    if not os.path.isdir(project):
        raise FileNotFoundError("No project uploaded.")
    out = os.path.join(root, "MR_REAN_FIXED_PROJECT.zip")
    if os.path.exists(out):
        os.remove(out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for base, dirs, files in os.walk(project):
            dirs[:] = [d for d in dirs if d not in {".git","node_modules","__pycache__",".venv","venv"}]
            for fn in files:
                path = os.path.join(base, fn)
                rel = os.path.relpath(path, project).replace(os.sep, "/")
                z.write(path, rel)
    return out

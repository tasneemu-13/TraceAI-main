import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "TraceAI_Project.zip"

exclude_dirs = {".venv", "venv", ".git", ".nicegui", "__pycache__", ".agents", ".gemini"}
exclude_files = {"TraceAI_Project.zip"}

print("Starting to compress project files...")
total_added = 0

with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(ROOT):
        # Modify dirs in-place to avoid descending into excluded folders
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file in exclude_files or file.endswith(".zip") or file.endswith(".log"):
                continue
            file_path = Path(root) / file
            rel_path = file_path.relative_to(ROOT)
            zipf.write(file_path, rel_path)
            total_added += 1

print(f"\nSuccessfully archived {total_added} files.")
print(f"ZIP file location: {ZIP_PATH}")

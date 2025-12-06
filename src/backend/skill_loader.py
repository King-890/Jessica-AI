import importlib
import json
from pathlib import Path


def load_skills(skills_dir: Path = Path("skills")):
    manifest_path = skills_dir / "skill_manifest.json"
    loaded = []
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            for m in manifest.get("skills", []):
                name = m.get("module")
                if not name:
                    continue
                try:
                    mod = importlib.import_module(f"skills.{name}")
                    loaded.append(mod)
                except Exception:
                    pass
        except Exception:
            pass
    else:
        # Fallback: load any python files in skills directory
        for p in skills_dir.glob("*.py"):
            if p.name == "__init__.py":
                continue
            try:
                mod = importlib.import_module(f"skills.{p.stem}")
                loaded.append(mod)
            except Exception:
                pass
    return loaded
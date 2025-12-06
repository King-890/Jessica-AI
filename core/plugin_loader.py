import json
import os
import importlib.util
from typing import List, Dict, Any

from data.db import add_plugin, list_plugins, update_plugin_config


PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")


def _load_config(path: str) -> Dict[str, Any] | None:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def discover_plugins() -> List[Dict[str, Any]]:
    os.makedirs(PLUGIN_ROOT, exist_ok=True)
    plugins: List[Dict[str, Any]] = []
    for entry in os.listdir(PLUGIN_ROOT):
        plugin_dir = os.path.join(PLUGIN_ROOT, entry)
        if not os.path.isdir(plugin_dir):
            continue
        cfg = _load_config(os.path.join(plugin_dir, "config.json"))
        main_py = os.path.join(plugin_dir, "main.py")
        if not cfg or not os.path.exists(main_py):
            continue
        plugins.append({
            "id": cfg.get("id") or entry,
            "name": cfg.get("name") or entry,
            "version": cfg.get("version") or "0.0.0",
            "category": cfg.get("category") or "utilities",
            "path": plugin_dir,
            "config": cfg,
        })
    return plugins


def import_plugin_main(module_path: str):
    try:
        spec = importlib.util.spec_from_file_location("plugin_main", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)  # type: ignore
        return module
    except Exception:
        return None


def sync_plugins_to_db() -> List[Dict[str, Any]]:
    found = discover_plugins()
    existing = {row[0]: row for row in list_plugins()}  # id -> row
    for p in found:
        pid = p["id"]
        cfg_json = json.dumps(p["config"]) if p.get("config") else None
        if pid in existing:
            if cfg_json:
                update_plugin_config(pid, cfg_json)
        else:
            add_plugin(pid, p["name"], True, cfg_json)
    return found
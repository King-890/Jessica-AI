import json
from typing import Protocol, List, Any
from data import db
from core.plugin_loader import discover_plugins, import_plugin_main
from core.plugin_runtime import Sandbox
import os


class PreProcessor(Protocol):
    def process(self, text: str) -> str: ...


class PostProcessor(Protocol):
    def process(self, text: str) -> str: ...


class CommandRouter(Protocol):
    def route(self, command: str, args: List[str]) -> tuple[str, List[str]]: ...


class LowercasePre:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def process(self, text: str) -> str:
        return text.lower() if self.enabled else text


class TruncatePost:
    def __init__(self, max_len: int = 500):
        self.max_len = max_len

    def process(self, text: str) -> str:
        return text[: self.max_len]


class PluginManager:
    def __init__(self):
        self._pre: List[PreProcessor] = []
        self._post: List[PostProcessor] = []
        self._routers: List[CommandRouter] = []
        self._hooks: List[Any] = []  # loaded plugins with lifecycle hooks
        self._sandbox = Sandbox()
        self.reload()

    def reload(self):
        self._pre.clear()
        self._post.clear()
        self._routers.clear()
        self._hooks.clear()
        for r in db.list_plugins():
            enabled = bool(r["enabled"])
            cfg = json.loads(r["config_json"]) if r["config_json"] else {}
            if r["id"] == "lowercase_pre":
                if enabled:
                    self._pre.append(LowercasePre(True))
            elif r["id"] == "truncate_post":
                if enabled:
                    self._post.append(TruncatePost(int(cfg.get("max_len", 500))))
            # Command routers can be added similarly

        # Load filesystem plugins with lifecycle hooks
        discovered = {p["id"]: p for p in discover_plugins()}
        for r in db.list_plugins():
            pid = r["id"]
            enabled = bool(r["enabled"])
            if not enabled:
                continue
            if pid in discovered:
                mod = import_plugin_main(os.path.join(discovered[pid]["path"], "main.py"))
                if mod:
                    plugin_cls = getattr(mod, "Plugin", None)
                    if plugin_cls:
                        try:
                            instance = plugin_cls()
                            # Call on_load in sandbox
                            self._sandbox.call(instance, "on_load")
                            self._hooks.append(instance)
                        except Exception:
                            continue

    def apply_pre(self, text: str) -> str:
        for p in self._pre:
            text = p.process(text)
        return text

    def apply_post(self, text: str) -> str:
        for p in self._post:
            text = p.process(text)
        return text

    def route_command(self, command: str, args: List[str]) -> tuple[str, List[str]]:
        for r in self._routers:
            command, args = r.route(command, args)
        return command, args

    def on_event(self, name: str, payload: Any | None = None) -> None:
        for h in self._hooks:
            self._sandbox.call(h, "on_event", name, payload)

    def on_command(self, name: str, args: List[str] | None = None) -> List[Any]:
        results: List[Any] = []
        for h in self._hooks:
            res = self._sandbox.call(h, "on_command", name, args or [])
            if res is not None:
                results.append(res)
        return results


plugin_manager = PluginManager()
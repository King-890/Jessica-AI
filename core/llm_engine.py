from typing import List, Tuple


UNITY_KEYWORDS = {
    "unity", "c#", "monobehaviour", "gameobject", "scriptableobject", "editor",
    "shader", "prefab", "scene", "navmesh", "rigidbody", "serializefield"
}


class LLMEngine:
    """Rule-based stub for Phase 1.

    - Echoes input while demonstrating context awareness using recent history.
    - Detects Unity-related discussions and prioritizes developer assistance tips.
    Replace with real LLM integration later.
    """

    def generate(self, text: str) -> str:
        return f"LLM stub received: {text}"

    def generate_with_context(self, text: str, history: List[Tuple[str, str]]) -> str:
        lower = text.lower()
        is_unity = any(k in lower for k in UNITY_KEYWORDS)

        trail = []
        for role, content in list(history)[-5:]:
            trail.append(f"{role}: {content}")
        context_snippet = " | ".join(trail) if trail else "(no recent context)"

        if is_unity:
            tips = (
                "Unity context detected. Consider: organize scripts with MonoBehaviours, use ScriptableObjects for data, "
                "profile with Unity Profiler, prefer async Addressables for asset loading, and write Editor tools for repetitive tasks."
            )
            return f"[Unity Assist] {tips} Input: '{text}'. Context: {context_snippet}"

        return f"[Contextual Reply] You said: '{text}'. Recent: {context_snippet}"
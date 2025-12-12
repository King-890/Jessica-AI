from typing import Dict, Any, Callable, Optional
from pathlib import Path
from .mcp_host import MCPHost
from src.rag.rag_manager import RAGManager
from src.training.data_collector import DataCollector
from src.model.tokenizer import SimpleTokenizer
from src.backend.ai_core import google_search
from src.model.gemini_client import GeminiClient

# NOTE: Torch is now lazy-loaded to save RAM!

class Brain:
    """
    Hybrid Brain: Defaults to Cloud LLM (Gemini) for high intelligence and low RAM.
    Falls back to Local Heuristics if offline/no key.
    """
    def __init__(self, config: Dict[str, Any], mcp_host: MCPHost, rag_manager: Optional[RAGManager] = None):
        self.config = config
        self.mcp_host = mcp_host
        self.rag_manager = rag_manager
        self.data_collector = DataCollector()
        self.mode = 'training'
        self.history = []

        # --- Initialize Cloud Backend (Gemini) ---
        print("🧠 Initializing Cloud Brain (Gemini Flash 1.5)...")
        self.gemini = GeminiClient()
        
        if self.gemini.is_available():
            print("   ✅ Google Gemini API Key Found. Running at 100% Intelligence.")
            self.use_cloud_llm = True
        else:
            print("   ⚠️ No Google API Key found in src/app_secrets.py.")
            print("   -> Running in Low-Power Heuristic Mode.")
            self.use_cloud_llm = False

        # --- Initialize Tokenizer (Lightweight) ---
        # Still needed for some local utilities
        self.tokenizer = SimpleTokenizer()
        
        self.local_model = None # Lazy load only if needed
        self.device = 'cpu'

        # --- Persona System ---
        self.personas = {
            "default": (
                "You are Jessica, a highly capable AI Assistant dedicated to helping the User build their Empire. "
                "You are professional, efficient, proactive, and autonomous. "
                "You have access to tools to manage files, research the web, and control the system."
            ),
            "ide": (
                "You are Jessica (IDE Mode), an expert Senior Software Engineer and Architect. "
                "Focus strictly on Code Quality, Architecture, and Implementation. "
                "Provide concise, copy-pasteable code blocks. Audit all code for bugs and security."
            ),
            "friend": (
                "You are Jessica (Friend Mode), a supportive and casual companion. "
                "Be empathetic, use casual language, and focus on the user's well-being and motivation. "
                "You are still helpful, but the tone is warm and personal."
            ),
            "helper": (
                "You are Jessica (Helper Mode), a dedicated executive assistant. "
                "Focus on organizing tasks, managing schedules, and executing commands efficiently. "
                "Be extremely brief and action-oriented."
            )
        }
        self.current_persona = "default"
        self.persona = self.personas["default"]

    def set_persona(self, role: str) -> bool:
        """Transform the AI into a specific role."""
        role_key = role.lower().strip()
        if role_key in self.personas:
            self.current_persona = role_key
            self.persona = self.personas[role_key]
            print(f"🦋 Brain transformed into: {role_key.upper()}")
            return True
        return False

    async def process_input(
        self,
        user_input: str,
        update_callback: Callable[[str], None] = None,
        confirmation_callback: Callable[[str, dict], bool] = None
    ) -> str:  # noqa: C901
        """
        Process input:
        1. Inject Persona + RAG/Tool Context via prompt.
        2. IF Cloud LLM available -> Send to Gemini.
        3. ELSE -> Use Heuristic Fallback.
        """
        context_accumulated = []
        print(f"🧠 Brain Process Input: '{user_input}'")
        
        # 0. RAG Context
        rag_context = ""
        if self.rag_manager and hasattr(self.rag_manager, 'get_context_for_query'):
            try:
                rag_context = self.rag_manager.get_context_for_query(user_input, top_k=2)
                if rag_context:
                    if update_callback:
                        update_callback("\n[Using RAG Knowledge]\n")
                    context_accumulated.append(f"Context from Knowledge Base:\n{rag_context}")
            except Exception:
                pass

        # 1. Heuristic Tool Use (Run tools locally first, then feed result to LLM)
        tool_output = await self._heuristic_tool_check(user_input, confirmation_callback, update_callback)
        if tool_output:
            context_accumulated.append(f"System Tool Result:\n{tool_output}")

        # 2. Construct Prompt
        full_user_message = f"User Request: {user_input}\n\n"
        if context_accumulated:
            full_user_message += "=== System Context ===\n" + "\n".join(context_accumulated)

        if update_callback:
            update_callback("[Thinking...]\n")

        # 3. GENERATE
        if self.use_cloud_llm:
            # --- CLOUD PATH (Smart) ---
            generated_text = self.gemini.generate(
                prompt=full_user_message,
                system_instruction=self.persona
            )
        else:
            # --- FALLBACK PATH (Dumb/Heuristic) ---
            # If we have tool output, show it.
            if tool_output:
                generated_text = f"I executed that command. Result:\n\n{tool_output}\n\n(Please add a Google API Key to src/app_secrets.py for me to better explain this.)"
            elif rag_context:
                 generated_text = f"I found this info locally:\n\n{rag_context}\n\n(Please add a Google API Key to src/app_secrets.py for reasoning capabilities.)"
            else:
                 generated_text = (
                    "I am currently in Low-Power Mode (No API Key). "
                    "Please add your GOOGLE_API_KEY to 'src/app_secrets.py' to unlock my full potential."
                    "\n\nI can still execute commands like: 'run command whoami' or 'search web ...'"
                )

        if update_callback:
            update_callback(generated_text)

        # 4. Save for Training
        self.data_collector.save_interaction(
            user_input=full_user_message,
            assistant_response=generated_text,
            context={"backend": "gemini" if self.use_cloud_llm else "heuristic"}
        )

        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": generated_text})

        return generated_text

    async def _heuristic_tool_check(
        self,
        user_input: str,
        confirmation_callback,
        update_callback
    ) -> Optional[str]:  # noqa: C901
        """
        Temporary logic to trigger MCP tools based on keywords.
        """
        user_lower = user_input.lower()

        # H. Persona / Transform Trigger
        import re
        transform_match = re.search(r"(become|transform into|switch to) (a |an )?(\w+)", user_input, re.IGNORECASE)
        if transform_match:
            target_role = transform_match.group(3).lower()
            # Handle "friend", "ide", "helper"
            if target_role in self.personas:
                self.set_persona(target_role)
                return f"Transformation Complete. I am now in {target_role.upper()} Mode.\n{self.personas[target_role]}"
            elif target_role == "default" or target_role == "normal":
                self.set_persona("default")
                return "Restored to Default Mode."

        # G. Web Search (More Flexible)
        import re
        # Heuristic: explicit "search" OR question words
        search_triggers = r"^(search|google|find)\b|^(what|where|who|how|when)\s+is\b|^(tell me about)\b"
        if re.search(search_triggers, user_lower):
            # Extract query: remove "search", "google", etc if present, otherwise use full string
            query = user_input
            match_explicit = re.search(r"^(search|google|find)\s+(.+)", user_input, re.IGNORECASE)
            if match_explicit:
                query = match_explicit.group(2).strip()
            # If question, use full string as query
            
            if len(query) > 3: # Avoid accidental Matches
                if update_callback: update_callback(f"[Searching Web: {query}]...")
                try:
                    return google_search(query)
                except Exception as e:
                    return f"Search Error: {e}"

        # A. Shell Execution (More Flexible)
        # Direct commands: whoami, ls, dir, pwd, date
        direct_cmds = ["whoami", "ls", "dir", "pwd", "date", "ipconfig"]
        cleaned_input = user_input.strip()
        if cleaned_input.lower() in direct_cmds:
             cmd = cleaned_input
             if update_callback: update_callback(f"[Executing: {cmd}]...")
             try:
                 from src.api.routes.shell import SafetyGuard
                 import subprocess
                 # SafetyGuard.check(cmd) # Basic cmds are safe
                 res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                 return f"Result:\n{res.stdout}"
             except Exception as e:
                 return f"Error: {e}"

        if "command" in user_lower or "exec" in user_lower or "run terminal" in user_lower:
            cmd_match = re.search(r"(run command|execute|exec|run)\s+(.+)", user_input, re.IGNORECASE)
            if cmd_match:
                cmd = cmd_match.group(2).strip()
                if confirmation_callback:
                    if not confirmation_callback("Execute Shell Command", {"command": cmd}):
                        if update_callback:
                            update_callback("[Command Execution Denied]")
                        return "User denied command execution."

                if update_callback:
                    update_callback(f"[Executing: {cmd}]...")
                try:
                    # Lazy Load SafetyGuard
                    from src.api.routes.shell import SafetyGuard
                    import subprocess
                    SafetyGuard.check(cmd)
                    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                    return f"Result: {res.stdout}"
                except Exception as e:
                    return f"Error: {e}"

        # D. List Files
        if "list files" in user_lower or "ls" == user_lower or "ls " in user_lower:
            import os
            target_dir = "."
            # extract path if provided e.g. "ls src"
            parts = user_input.split()
            if len(parts) > 1 and (parts[0].lower() == "ls" or parts[0].lower() == "list"):
                target_dir = parts[-1]

            if update_callback:
                update_callback(f"[Listing directory: {target_dir}]...")
            try:
                files = os.listdir(target_dir)
                return f"Files in {target_dir}:\n" + "\n".join(files[:50]) + ("\n... (truncated)" if len(files) > 50 else "")
            except Exception as e:
                return f"List Error: {e}"

        # E. Read File (Improved)
        if "read file" in user_lower or "cat " in user_lower:
            import re
            # match "read file <path>" or "cat <path>"
            match = re.search(r"(read file|cat)\s+(.+)", user_input, re.IGNORECASE)
            if match:
                path = match.group(2).strip()
                import os

                if update_callback:
                    update_callback(f"[Reading file: {path}]...")
                try:
                    if os.path.exists(path) and os.path.isfile(path):
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read(4000)  # Limit char count
                        return f"File Content ({path}):\n{content}"
                    else:
                        return f"File not found: {path}"
                except Exception as e:
                    return f"Read Error: {e}"

        # F. Search Code
        if "search code" in user_lower or "grep" in user_lower:
            import re
            import os
            match = re.search(r"(search code|grep)\s+(.+)", user_input, re.IGNORECASE)
            if match:
                query = match.group(2).strip()
                if update_callback:
                    update_callback(f"[Searching codebase for: {query}]...")
                try:
                    matches = []
                    for root, dirs, files in os.walk("."):
                        if ".git" in dirs: dirs.remove(".git")
                        if "__pycache__" in dirs: dirs.remove("__pycache__")
                        for file in files:
                            if file.endswith(('.py', '.md', '.txt', '.yaml', '.json')):
                                __path = os.path.join(root, file)
                                try:
                                    with open(__path, 'r', encoding='utf-8', errors='ignore') as f:
                                        for i, line in enumerate(f):
                                            if query in line:
                                                matches.append(f"{__path}:{i + 1}: {line.strip()[:100]}")
                                                if len(matches) > 15: break
                                except Exception: pass
                        if len(matches) > 15: break

                    if matches:
                        return f"Search Results for '{query}':\n" + "\n".join(matches)
                    else:
                        return f"No matches found for '{query}'"
                except Exception as e:
                    return f"Search Error: {e}"

        # C. Read URL (Web Ingestion)
        if "read url" in user_lower or "ingest url" in user_lower:
            import re
            url_match = re.search(r"(read|ingest) url\s+(http[s]?://\S+)", user_input, re.IGNORECASE)
            if url_match:
                url = url_match.group(2).strip()
                if self.rag_manager:
                    if update_callback:
                        update_callback(f"[Reading URL: {url}]...")
                    try:
                        self.rag_manager.ingest_web_page(url)
                        return f"Successfully read and memorized: {url}"
                    except Exception as e:
                        return f"Failed to read URL: {e}"
                else:
                    return "RAG Manager not active."

        # B. File Writing (Handled by Gemini if smart, or heuristic if robust)
        # We leave basic file writing here just in case heuristic mode needs it
        if "create file" in user_lower or "write file" in user_lower:
            # Basic parsing if Gemini didn't catch it
             pass 

        return None

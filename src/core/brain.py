import torch
from typing import Dict, Any, Callable, Optional
from pathlib import Path
from .mcp_host import MCPHost
from src.rag.rag_manager import RAGManager
from src.training.data_collector import DataCollector
from src.model.transformer import JessicaGPT
from src.model.tokenizer import SimpleTokenizer
from src.backend.ai_core import google_search


class Brain:
    """
    Pure Custom Brain with Tool Execution & Confirmation System.
    """
    def __init__(self, config: Dict[str, Any], mcp_host: MCPHost, rag_manager: Optional[RAGManager] = None):
        self.config = config
        self.mcp_host = mcp_host
        self.rag_manager = rag_manager
        self.data_collector = DataCollector()
        self.mode = 'training'

        # --- Initialize Local Backend (Custom) ---
        print("🧠 Initializing Local JessicaGPT (Custom, No External API)...")
        print("   -> Initializing Tokenizer...")
        self.tokenizer = SimpleTokenizer()

        print(f"   -> Initializing Model (Vocab: {self.tokenizer.vocab_size})...")
        # Small model for responsiveness
        self.local_model = JessicaGPT(vocab_size=self.tokenizer.vocab_size, n_embd=128, n_head=4, n_layer=4)

        # --- Load Trained Weights ---
        llm_conf = self.config.get("llm", {})
        model_path = llm_conf.get("model_path")
        if model_path:
            p = Path(model_path)
            if p.exists():
                print(f"   -> 💾 Loading Weights from {p}...")
                try:
                    # Map location ensures we can load GPU model on CPU if needed
                    state_dict = torch.load(p, map_location='cpu' if not torch.cuda.is_available() else None)
                    self.local_model.load_state_dict(state_dict)
                    print("   -> Weights loaded successfully.")
                except Exception as e:
                    print(f"   -> ❌ Failed to load weights: {e}")
            else:
                print(f"   -> ⚠️ Model file not found at {p}. Using random weights.")

        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"   -> Moving to device: {self.device}")
        self.local_model.to(self.device)
        self.local_model.eval()
        print("   -> Brain initialized.")

        self.history = []

        # --- Cloud Configuration ---
        self.cloud_mode = self.config.get("cloud_mode", False)
        self.cloud_url = self.config.get("cloud_url", "http://localhost:8080")

        if self.cloud_mode:
            print(f"☁️ Cloud Mode ENABLED. Connected to: {self.cloud_url}")

        # --- Persona ---
        self.persona = (
            "You are Jessica, a highly capable AI Assistant dedicated to helping the User build their Empire. "
            "You are professional, efficient, and proactive."
        )

        # Heuristic Mode Flag: If True, we don't rely on the model for generation (it's random/untrained)
        # In a real scenario, we'd check if weight file existed, but for now let's assume if it's small/random it's untrained
        self.is_model_untrained = True  # Default to True for safety in this phase
        if model_path and Path(model_path).exists():
            self.is_model_untrained = False  # Assume trained if explicit weights loaded

    def set_mode(self, mode: str):
        print(f"Brain switched to {mode.upper()} mode.")

    async def process_input(
        self,
        user_input: str,
        update_callback: Callable[[str], None] = None,
        confirmation_callback: Callable[[str, dict], bool] = None
    ) -> str:  # noqa: C901
        """
        Process input:
        1. Inject Persona + RAG/Tool Context via prompt.
        2. IF the model *generates* a tool call (future training), execute it.
        3. For Phase 2/3 MVP: Heuristic triggers.
        """
        context_accumulated = []

        # 0. Inject Persona
        context_accumulated.append(f"System: {self.persona}")

        # 1. RAG Context
        if self.rag_manager and hasattr(self.rag_manager, 'get_context_for_query'):
            try:
                rag_context = self.rag_manager.get_context_for_query(user_input, top_k=2)
                if rag_context:
                    if update_callback:
                        update_callback("\n[Using RAG Knowledge]\n")
                    context_accumulated.append(f"Context from Knowledge Base:\n{rag_context}")
            except Exception:
                pass

        # 2. Heuristic Tool Use
        tool_output = await self._heuristic_tool_check(user_input, confirmation_callback, update_callback)
        if tool_output:
            context_accumulated.append(f"Tool Output:\n{tool_output}")

        # 3. Feed to Model or Heuristic Fallback
        full_prompt = "\n".join(context_accumulated + [f"User: {user_input}"])

        if update_callback:
            update_callback("[Thinking...]\n")

        if self.is_model_untrained:
            # Fallback: Don't let random model hallucinate.
            # If we have RAG context, show it. If not, give generic response.
            if "Context from Knowledge Base" in full_prompt:
                generated_text = "I found this in my memory:\n\n" + rag_context
            else:
                generated_text = (
                    "I am currently running in local mode without training data. "
                    "I can execute commands (e.g. 'run command whoami') or list files, but I cannot generate conversation yet."
                )
        else:
            generated_text = self._generate(full_prompt)

        if update_callback:
            update_callback(generated_text)

        # 4. Save for Training
        self.data_collector.save_interaction(
            user_input=full_prompt,
            assistant_response=generated_text,
            context={"backend": "custom_gpt", "rag_used": bool(context_accumulated)}
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

        if "search" in user_lower:
            # G. Web Search
            # Simple heuristic: "search <query>"
            import re
            match = re.search(r"(search|google)\s+(.+)", user_input, re.IGNORECASE)
            if match:
                query = match.group(2).strip()
                if update_callback: update_callback(f"[Searching Web: {query}]...")
                try:
                    return google_search(query)
                except Exception as e:
                    return f"Search Error: {e}"

        # A. Shell Execution
        if "command" in user_lower or "exec" in user_lower or "run terminal" in user_lower:
            import re
            cmd_match = re.search(r"(run command|execute|exec)\s+(.+)", user_input, re.IGNORECASE)
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
                    from src.api.routes.shell import SafetyGuard
                    import subprocess
                    SafetyGuard.check(cmd)
                    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                    return f"Shell Result: {res.stdout}"
                except Exception as e:
                    return f"Shell Error: {e}"

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
                            content = f.read(2000)  # Limit to 2k chars for chat visual
                            if len(f.read(1)) > 0:
                                content += "\n... (truncated)"
                        return f"File Content ({path}):\n```\n{content}\n```"
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
                    # Simple grep using rg if available, or python walk
                    # Let's use python walk for "pure local" reliability without rg dependency
                    matches = []
                    for root, dirs, files in os.walk("."):
                        if ".git" in dirs:
                            dirs.remove(".git")
                        if "__pycache__" in dirs:
                            dirs.remove("__pycache__")
                        for file in files:
                            if file.endswith(('.py', '.md', '.txt', '.yaml', '.json')):
                                __path = os.path.join(root, file)
                                try:
                                    with open(__path, 'r', encoding='utf-8', errors='ignore') as f:
                                        for i, line in enumerate(f):
                                            if query in line:
                                                matches.append(f"{__path}:{i + 1}: {line.strip()[:100]}")
                                                if len(matches) > 10:
                                                    break
                                except Exception:
                                    pass
                        if len(matches) > 10:
                            break

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

        # B. File Writing
        if "create file" in user_lower or "write file" in user_lower:
            parts = user_input.split("content")
            if len(parts) >= 1:
                filename = "test.txt"
                content = "Hello Empire"
                words = user_input.split()
                try:
                    idx = words.index("file")
                    filename = words[idx + 1]
                except Exception:
                    pass

                if confirmation_callback:
                    if not confirmation_callback("Write File", {"path": filename, "content": "..."}):
                        return "User denied file write."

                if update_callback:
                    update_callback(f"[Writing File: {filename}]...")
                try:
                    # Mock write
                    with open(filename, 'w') as f:
                        f.write(content)
                    return f"File Written: {filename}"
                except Exception as e:
                    return f"File Error: {e}"

        return None

    def _generate(self, text: str) -> str:
        """Run generation on local model OR Cloud API"""
        if self.cloud_mode:
            try:
                import requests
                print(f"☁️ Sending to Cloud Brain: {self.cloud_url}/chat")
                response = requests.post(
                    f"{self.cloud_url}/chat",
                    json={"message": text, "user_id": "client_app"},
                    timeout=30
                )
                if response.status_code == 200:
                    return response.json().get("response", "[Empty Cloud Response]")
                else:
                    return f"[Cloud Error {response.status_code}]: {response.text}"
            except Exception as e:
                return f"[Cloud Connection Failed]: {e}"

        # --- Local Fallback ---
        input_ids = self.tokenizer.encode(text)
        if len(input_ids) > 200:
            input_ids = input_ids[-200:]

        input_tensor = torch.tensor(input_ids, dtype=torch.long, device=self.device).unsqueeze(0)

        with torch.no_grad():
            output_ids = self.local_model.generate(input_tensor, max_new_tokens=60)

        generated_ids = output_ids[0].tolist()[len(input_ids):]
        return self.tokenizer.decode(generated_ids)

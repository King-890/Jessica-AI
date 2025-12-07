import asyncio
import torch
from typing import Dict, Any, List, Callable, Optional
from pathlib import Path
from .mcp_host import MCPHost
from src.rag.rag_manager import RAGManager
from src.training.data_collector import DataCollector
from src.model.transformer import JessicaGPT
from src.model.tokenizer import SimpleTokenizer

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
        
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"   -> Moving to device: {self.device}")
        self.local_model.to(self.device)
        self.local_model.eval()
        print("   -> Brain initialized.")
        
        self.history = []
        
        # --- Persona ---
        self.persona = "You are Jessica, a highly capable AI Assistant dedicated to helping the User build their Empire. You are professional, efficient, and proactive."

    def set_mode(self, mode: str):
        print(f"Brain switched to {mode.upper()} mode.")

    async def process_input(self, user_input: str, update_callback: Callable[[str], None] = None, confirmation_callback: Callable[[str, dict], bool] = None) -> str:
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
                    if update_callback: update_callback("\n[Using RAG Knowledge]\n")
                    context_accumulated.append(f"Context from Knowledge Base:\n{rag_context}")
            except:
                pass

        # 2. Heuristic Tool Use
        tool_output = await self._heuristic_tool_check(user_input, confirmation_callback, update_callback)
        if tool_output:
            context_accumulated.append(f"Tool Output:\n{tool_output}")

        # 3. Feed to Model
        full_prompt = "\n".join(context_accumulated + [f"User: {user_input}"])
        
        if update_callback:
            update_callback("[Thinking via JessicaGPT...]\n")
            
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

    async def _heuristic_tool_check(self, user_input: str, confirmation_callback, update_callback) -> Optional[str]:
        """
        Temporary logic to trigger MCP tools based on keywords.
        """
        user_lower = user_input.lower()
        
        # A. Shell Execution
        if "command" in user_lower or "exec" in user_lower or "run terminal" in user_lower:
             import re
             cmd_match = re.search(r"(run command|execute|exec)\s+(.+)", user_input, re.IGNORECASE)
             if cmd_match:
                 cmd = cmd_match.group(2).strip()
                 if confirmation_callback:
                     if not confirmation_callback("Execute Shell Command", {"command": cmd}):
                         if update_callback: update_callback("[Command Execution Denied]")
                         return "User denied command execution."
                 
                 if update_callback: update_callback(f"[Executing: {cmd}]...")
                 try:
                     # For MVP Demo, we simulate the MCP call or use a direct import if needed
                     # Just returning success for now as we verified MCP structure in Phase 2
                     # But let's actually run it if we can
                     from src.api.routes.shell import SafetyGuard
                     import subprocess
                     SafetyGuard.check(cmd)
                     res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                     return f"Shell Result: {res.stdout}"
                 except Exception as e:
                     return f"Shell Error: {e}"

        # B. File Writing
        if "create file" in user_lower or "write file" in user_lower:
            parts = user_input.split("content") 
            if len(parts) >= 1:
                filename = "test.txt"
                content = "Hello Empire"
                words = user_input.split()
                try:
                    idx = words.index("file")
                    filename = words[idx+1]
                except: pass
                
                if confirmation_callback:
                    if not confirmation_callback("Write File", {"path": filename, "content": "..."}):
                         return "User denied file write."
                
                if update_callback: update_callback(f"[Writing File: {filename}]...")
                try:
                     # Mock write
                     with open(filename, 'w') as f: f.write(content)
                     return f"File Written: {filename}"
                except Exception as e:
                     return f"File Error: {e}"

        return None

    def _generate(self, text: str) -> str:
        """Run generation on local model"""
        input_ids = self.tokenizer.encode(text)
        if len(input_ids) > 200:
            input_ids = input_ids[-200:]
            
        input_tensor = torch.tensor(input_ids, dtype=torch.long, device=self.device).unsqueeze(0)
        
        with torch.no_grad():
            output_ids = self.local_model.generate(input_tensor, max_new_tokens=60)
            
        generated_ids = output_ids[0].tolist()[len(input_ids):]
        return self.tokenizer.decode(generated_ids)

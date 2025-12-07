import asyncio
import os
from typing import Dict, List, Any, Optional
from contextlib import AsyncExitStack

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    ClientSession = Any
    StdioServerParameters = Any
    print("Warning: mcp library not found. MCP Host disabled.")

class MCPHost:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.servers: Dict[str, Any] = {}
        self.exit_stack = AsyncExitStack()

    async def start(self):
        if not MCP_AVAILABLE:
            return

        server_configs = self.config.get('mcp_servers', {})
        for name, server_config in server_configs.items():
            command = server_config.get('command')
            args = server_config.get('args', [])
            env = server_config.get('env', {})
            
            # Merge with current environment
            full_env = os.environ.copy()
            full_env.update(env)

            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=full_env
            )

            try:
                # Create the client connection
                stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
                read, write = stdio_transport
                session = await self.exit_stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                
                self.servers[name] = session
                print(f"Connected to MCP server: {name}")
            except Exception as e:
                print(f"Failed to connect to MCP server {name}: {e}")

    async def get_tools(self) -> List[Dict[str, Any]]:
        all_tools = []
        if not MCP_AVAILABLE:
            return all_tools

        for name, session in self.servers.items():
            try:
                tools_result = await session.list_tools()
                for tool in tools_result.tools:
                    all_tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                        "server": name # Keep track of which server provides it
                    })
            except Exception as e:
                print(f"Error listing tools for server {name}: {e}")
        return all_tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP not available")

        if server_name not in self.servers:
            raise ValueError(f"Server {server_name} not found")
        
        session = self.servers[server_name]
        result = await session.call_tool(tool_name, arguments)
        return result

    async def stop(self):
        await self.exit_stack.aclose()

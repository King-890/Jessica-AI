#!/usr/bin/env python3
"""
Shell Command MCP Server
Executes shell commands with safety checks and confirmations.
"""

import asyncio
import os
import sys
import subprocess
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Initialize server
app = Server("shell-command")

# Command risk assessment
HIGH_RISK_COMMANDS = [
    "rm", "del", "format", "shutdown", "reboot", "mkfs",
    "dd", "fdisk", "parted", "kill", "killall"
]

MEDIUM_RISK_COMMANDS = [
    "git push", "npm publish", "pip install", "apt install",
    "brew install", "choco install", "move", "mv", "cp"
]

def assess_command_risk(command: str) -> str:
    """Assess the risk level of a command"""
    command_lower = command.lower().strip()
    
    # Check for high risk commands
    for risky_cmd in HIGH_RISK_COMMANDS:
        if command_lower.startswith(risky_cmd) or f" {risky_cmd} " in command_lower:
            return "HIGH"
    
    # Check for medium risk commands
    for medium_cmd in MEDIUM_RISK_COMMANDS:
        if command_lower.startswith(medium_cmd) or f" {medium_cmd} " in command_lower:
            return "MEDIUM"
    
    return "LOW"

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available shell command tools"""
    return [
        Tool(
            name="execute_command",
            description="Execute a shell command and return its output. "
                       "Commands are assessed for risk level. HIGH and MEDIUM risk commands require confirmation. "
                       "The command runs with a 30-second timeout by default. "
                       "Use this for running builds, tests, git commands, and other shell operations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    },
                    "working_directory": {
                        "type": "string",
                        "description": "Working directory for command execution (optional, defaults to current directory)"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Timeout in seconds (optional, defaults to 30)"
                    }
                },
                "required": ["command"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    
    if name == "execute_command":
        command = arguments["command"]
        cwd = arguments.get("working_directory", ".")
        timeout = arguments.get("timeout", 30)
        
        # Assess risk
        risk_level = assess_command_risk(command)
        
        # If HIGH or MEDIUM risk, require confirmation
        if risk_level in ["HIGH", "MEDIUM"]:
            return [TextContent(
                type="text",
                text=f"CONFIRMATION_REQUIRED:execute_command:{command}:{cwd}:{risk_level}"
            )]
        
        # LOW risk - execute immediately
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = f"Exit Code: {result.returncode}\n\n"
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            
            return [TextContent(type="text", text=output)]
        
        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text=f"Error: Command timed out after {timeout} seconds")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error executing command: {str(e)}")]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    print("Shell command server starting...", file=sys.stderr)
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())

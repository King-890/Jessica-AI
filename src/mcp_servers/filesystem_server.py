#!/usr/bin/env python3
"""
Custom Filesystem MCP Server with Write Capabilities
Extends the standard filesystem server with write, delete, and modify operations.
All dangerous operations require user confirmation.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Initialize server
app = Server("filesystem-extended")

# Allowed root directory (passed as command line argument)
ALLOWED_ROOT = None

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available filesystem tools"""
    return [
        Tool(
            name="read_file",
            description="Read the complete contents of a file from the file system. "
                       "Handles various text encodings and provides detailed error messages "
                       "if the file cannot be read. Use this tool when you need to examine "
                       "the contents of a single file. Only works within allowed directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read (relative to allowed root)"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="read_multiple_files",
            description="Read the contents of multiple files simultaneously. "
                       "This is more efficient than reading files one by one when you need "
                       "to analyze or compare multiple files. Each file's content is returned "
                       "with its path as a reference. Failed reads for individual files won't "
                       "stop the entire operation. Only works within allowed directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of file paths to read"
                    }
                },
                "required": ["paths"]
            }
        ),
        Tool(
            name="write_file",
            description="Create a new file or completely overwrite an existing file with new content. "
                       "⚠️ REQUIRES CONFIRMATION. Use with caution as it will overwrite existing files without warning. "
                       "Best for creating new files or completely replacing file contents. "
                       "Only works within allowed directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path where the file should be written"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="list_directory",
            description="Get a detailed listing of all files and directories in a specified path. "
                       "Results clearly distinguish between files and directories with [FILE] and [DIR] prefixes. "
                       "This tool is essential for understanding directory structure and finding specific files. "
                       "Only works within allowed directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory to list (relative to allowed root)"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="create_directory",
            description="Create a new directory or ensure a directory exists. "
                       "Can create multiple nested directories in one operation. "
                       "If the directory already exists, this operation will succeed silently. "
                       "Perfect for setting up directory structures for projects or ensuring paths exist. "
                       "Only works within allowed directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path of the directory to create"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="delete_file",
            description="Permanently delete a file from the filesystem. "
                       "⚠️ REQUIRES CONFIRMATION. This action cannot be undone. "
                       "Only works within allowed directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to delete"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="delete_directory",
            description="Permanently delete a directory and all its contents. "
                       "⚠️ REQUIRES CONFIRMATION. This action cannot be undone and will delete all files and subdirectories. "
                       "Only works within allowed directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory to delete"
                    }
                },
                "required": ["path"]
            }
        )
    ]

def validate_path(path: str) -> Path:
    """Validate that path is within allowed root directory"""
    if ALLOWED_ROOT is None:
        raise ValueError("No allowed root directory configured")
    
    # Resolve to absolute path
    requested_path = Path(path)
    if not requested_path.is_absolute():
        requested_path = ALLOWED_ROOT / requested_path
    
    requested_path = requested_path.resolve()
    
    # Check if within allowed root
    try:
        requested_path.relative_to(ALLOWED_ROOT)
    except ValueError:
        raise PermissionError(f"Access denied: {path} is outside allowed directory")
    
    return requested_path

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    
    try:
        if name == "read_file":
            path = validate_path(arguments["path"])
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return [TextContent(type="text", text=content)]
        
        elif name == "read_multiple_files":
            results = []
            for file_path in arguments["paths"]:
                try:
                    path = validate_path(file_path)
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    results.append(f"=== {file_path} ===\n{content}\n")
                except Exception as e:
                    results.append(f"=== {file_path} ===\nError: {str(e)}\n")
            return [TextContent(type="text", text="\n".join(results))]
        
        elif name == "write_file":
            path = validate_path(arguments["path"])
            content = arguments["content"]
            
            # Return confirmation request
            return [TextContent(
                type="text",
                text=f"CONFIRMATION_REQUIRED:write_file:{path}:{len(content)}"
            )]
        
        elif name == "list_directory":
            path = validate_path(arguments["path"])
            if not path.is_dir():
                raise NotADirectoryError(f"{path} is not a directory")
            
            entries = []
            for entry in sorted(path.iterdir()):
                prefix = "[DIR]" if entry.is_dir() else "[FILE]"
                entries.append(f"{prefix} {entry.name}")
            
            return [TextContent(type="text", text="\n".join(entries) if entries else "(empty directory)")]
        
        elif name == "create_directory":
            path = validate_path(arguments["path"])
            path.mkdir(parents=True, exist_ok=True)
            return [TextContent(type="text", text=f"Directory created: {path}")]
        
        elif name == "delete_file":
            path = validate_path(arguments["path"])
            
            # Return confirmation request
            return [TextContent(
                type="text",
                text=f"CONFIRMATION_REQUIRED:delete_file:{path}"
            )]
        
        elif name == "delete_directory":
            path = validate_path(arguments["path"])
            
            # Return confirmation request
            return [TextContent(
                type="text",
                text=f"CONFIRMATION_REQUIRED:delete_directory:{path}"
            )]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    global ALLOWED_ROOT
    
    # Get allowed root from command line
    if len(sys.argv) > 1:
        ALLOWED_ROOT = Path(sys.argv[1]).resolve()
    else:
        ALLOWED_ROOT = Path.cwd()
    
    print(f"Filesystem server starting with root: {ALLOWED_ROOT}", file=sys.stderr)
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
MATLAB MCP Server - Subprocess Version
Modified to work in WSL by using MATLAB command line instead of MATLAB Engine
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Configuration
MATLAB_PATH = os.getenv("MATLAB_PATH", "/mnt/c/Program Files/MATLAB/R2024a")
MATLAB_EXECUTABLE = os.path.join(MATLAB_PATH, "bin", "matlab.exe")

# Create a directory for MATLAB scripts if it doesn't exist
MATLAB_DIR = Path("matlab_scripts")
MATLAB_DIR.mkdir(exist_ok=True)

def run_matlab_command(command: str, script_path: Optional[str] = None) -> Dict[str, Any]:
    """Run a MATLAB command using subprocess."""
    try:
        if script_path:
            script_dir = os.path.dirname(script_path)
            script_name = os.path.basename(script_path).replace('.m', '')
            full_command = f"cd('{script_dir}'); {script_name}"
        else:
            full_command = command
        
        result = subprocess.run(
            [MATLAB_EXECUTABLE, "-batch", full_command],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return {
            "output": result.stdout,
            "error": result.stderr,
            "success": result.returncode == 0,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "output": "",
            "error": "MATLAB command timed out after 60 seconds",
            "success": False,
            "return_code": -1
        }
    except Exception as e:
        return {
            "output": "",
            "error": f"Error running MATLAB: {str(e)}",
            "success": False,
            "return_code": -1
        }

# Initialize the MCP server
server = Server("matlab-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available MATLAB tools."""
    return [
        types.Tool(
            name="execute_matlab_command",
            description="Execute a MATLAB command directly",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "MATLAB command to execute"
                    }
                },
                "required": ["command"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls."""
    if name == "execute_matlab_command":
        command = arguments["command"]
        result = run_matlab_command(command)
        
        response = f"MATLAB Command: {command}\n\n"
        if result["success"]:
            response += f"Output:\n{result['output']}"
            if result["error"]:
                response += f"\n\nWarnings:\n{result['error']}"
        else:
            response += f"Error:\n{result['error']}"
        
        return [types.TextContent(type="text", text=response)]
    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="matlab-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    if not os.path.exists(MATLAB_EXECUTABLE):
        print(f"Error: MATLAB executable not found at {MATLAB_EXECUTABLE}", file=sys.stderr)
        sys.exit(1)
    
    test_result = run_matlab_command("disp('MATLAB MCP Server Ready')")
    if not test_result["success"]:
        print(f"Error: Unable to run MATLAB: {test_result['error']}", file=sys.stderr)
        sys.exit(1)
    
    print("MATLAB MCP Server starting...", file=sys.stderr)
    asyncio.run(main())

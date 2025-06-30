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
    """
    Run a MATLAB command using subprocess.
    
    Args:
        command: MATLAB command to run
        script_path: Optional path to script file
        
    Returns:
        Dictionary with output, error, and success status
    """
    try:
        # Prepare the full command
        if script_path:
            # For script execution, change to the script directory and run
            script_dir = os.path.dirname(script_path)
            script_name = os.path.basename(script_path).replace('.m', '')
            full_command = f"cd('{script_dir}'); {script_name}; exit"
        else:
            full_command = f"{command}; exit"
        
        # Run MATLAB with the command
        result = subprocess.run(
            [MATLAB_EXECUTABLE, "-batch", full_command],
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
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
            name="create_matlab_script",
            description="Create a new MATLAB script file",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_name": {
                        "type": "string",
                        "description": "Name of the script (without .m extension)"
                    },
                    "code": {
                        "type": "string",
                        "description": "MATLAB code to save"
                    }
                },
                "required": ["script_name", "code"]
            }
        ),
        types.Tool(
            name="create_matlab_function",
            description="Create a new MATLAB function file",
            inputSchema={
                "type": "object",
                "properties": {
                    "function_name": {
                        "type": "string",
                        "description": "Name of the function (without .m extension)"
                    },
                    "code": {
                        "type": "string",
                        "description": "MATLAB function code"
                    }
                },
                "required": ["function_name", "code"]
            }
        ),
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
        ),
        types.Tool(
            name="execute_matlab_script",
            description="Execute a MATLAB script and return results",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_name": {
                        "type": "string",
                        "description": "Name of the script to execute (without .m extension)"
                    }
                },
                "required": ["script_name"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls."""
    
    if name == "create_matlab_script":
        script_name = arguments["script_name"]
        code = arguments["code"]
        
        # Validate script name
        if not script_name.replace('_', '').isalnum():
            return [types.TextContent(
                type="text",
                text=f"Error: Script name '{script_name}' must be a valid MATLAB identifier"
            )]
        
        # Create script file
        script_path = MATLAB_DIR / f"{script_name}.m"
        try:
            script_path.write_text(code)
            return [types.TextContent(
                type="text",
                text=f"Created MATLAB script: {script_path.absolute()}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error creating script: {str(e)}"
            )]
    
    elif name == "create_matlab_function":
        function_name = arguments["function_name"]
        code = arguments["code"]
        
        # Validate function name
        if not function_name.replace('_', '').isalnum():
            return [types.TextContent(
                type="text",
                text=f"Error: Function name '{function_name}' must be a valid MATLAB identifier"
            )]
        
        # Create function file
        function_path = MATLAB_DIR / f"{function_name}.m"
        try:
            function_path.write_text(code)
            return [types.TextContent(
                type="text",
                text=f"Created MATLAB function: {function_path.absolute()}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error creating function: {str(e)}"
            )]
    
    elif name == "execute_matlab_command":
        command = arguments["command"]
        
        result = run_matlab_command(command)
        
        response = f"MATLAB Command: {command}\n\n"
        if result["success"]:
            response += f"Output:\n{result['output']}"
            if result["error"]:
                response += f"\n\nWarnings/Messages:\n{result['error']}"
        else:
            response += f"Error (Return code: {result['return_code']}):\n{result['error']}"
            if result["output"]:
                response += f"\n\nOutput:\n{result['output']}"
        
        return [types.TextContent(type="text", text=response)]
    
    elif name == "execute_matlab_script":
        script_name = arguments["script_name"]
        script_path = MATLAB_DIR / f"{script_name}.m"
        
        if not script_path.exists():
            return [types.TextContent(
                type="text",
                text=f"Error: Script '{script_name}.m' not found in {MATLAB_DIR}"
            )]
        
        result = run_matlab_command("", str(script_path))
        
        response = f"Executed MATLAB script: {script_name}.m\n\n"
        if result["success"]:
            response += f"Output:\n{result['output']}"
            if result["error"]:
                response += f"\n\nWarnings/Messages:\n{result['error']}"
        else:
            response += f"Error (Return code: {result['return_code']}):\n{result['error']}"
            if result["output"]:
                response += f"\n\nOutput:\n{result['output']}"
        
        return [types.TextContent(type="text", text=response)]
    
    else:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

async def main():
    # Run the server using stdin/stdout streams
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
    # Test MATLAB availability
    if not os.path.exists(MATLAB_EXECUTABLE):
        print(f"Error: MATLAB executable not found at {MATLAB_EXECUTABLE}", file=sys.stderr)
        print("Please set MATLAB_PATH environment variable", file=sys.stderr)
        sys.exit(1)
    
    # Test MATLAB execution
    test_result = run_matlab_command("disp('MATLAB MCP Server Ready')")
    if not test_result["success"]:
        print(f"Error: Unable to run MATLAB: {test_result['error']}", file=sys.stderr)
        sys.exit(1)
    
    print("MATLAB MCP Server starting...", file=sys.stderr)
    asyncio.run(main())
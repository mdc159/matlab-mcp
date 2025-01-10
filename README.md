# MATLAB MCP Server

This Model Context Protocol (MCP) server provides integration with MATLAB, allowing you to create and execute MATLAB scripts and functions through Claude or other MCP clients.

## Setup Requirements

- Python 3.11 (Python 3.13 and 3.12 are not currently supported by MATLAB Engine)
- MATLAB R2024a (or compatible version)
- uv package manager

## Installation

1. Create and set up the Python environment:
```bash
# Pin Python version
uv python pin 3.11

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install MCP
uv add "mcp[cli]"
```

2. Install MATLAB Engine
The MATLAB Engine will be installed automatically when the server first runs, using the MATLAB installation specified in the `MATLAB_PATH` environment variable.

## Directory Structure

- `matlab_server.py`: The main MCP server implementation
- `matlab_scripts/`: Directory where all MATLAB scripts and functions are saved (created automatically)
- `pyproject.toml`: Python project configuration
- `.python-version`: Specifies Python version for uv

## Claude Desktop Integration

1. Open your Claude Desktop configuration:
```bash
# On macOS
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

2. Add the MATLAB server configuration:
```json
{
    "mcpServers": {
        "matlab": {
            "command": "uv",
            "args": [
                "--directory",
                "/absolute/path/to/matlab-mcp",
                "run",
                "matlab_server.py"
            ],
            "env": {
                "MATLAB_PATH": "/Applications/MATLAB_R2024a.app"
            }
        }
    }
}
```

Make sure to:
- Replace `/absolute/path/to/matlab-mcp` with the actual path to your project directory
- Verify the `MATLAB_PATH` points to your MATLAB installation
- Use absolute paths (not relative)

## Features

The server provides several tools:

1. `create_matlab_script`: Create a new MATLAB script file
   - Scripts are saved in the `matlab_scripts` directory
   - File names must be valid MATLAB identifiers

2. `create_matlab_function`: Create a new MATLAB function file
   - Functions are saved in the `matlab_scripts` directory
   - Must include valid function definition

3. `execute_matlab_script`: Run a MATLAB script and get results
   - Returns output text, generated figures, and workspace variables
   - Can pass arguments to scripts

4. `call_matlab_function`: Call a MATLAB function with arguments
   - Returns function output and any generated figures

## Testing

You can test the server using the MCP Inspector:
```bash
# Make sure you're in your virtual environment
source .venv/bin/activate

# Run the inspector
MATLAB_PATH=/Applications/MATLAB_R2024a.app mcp dev matlab_server.py
```

Example test script:
```matlab
t = 0:0.01:2*pi;
y = sin(t);
plot(t, y);
title('Test Plot');
xlabel('Time');
ylabel('Amplitude');
```

## Script Storage

- All MATLAB scripts and functions are saved in the `matlab_scripts` directory
- This directory is created automatically when the server starts
- Files are named `<script_name>.m` or `<function_name>.m`
- The directory is in the same location as `matlab_server.py`

## Environment Variables

- `MATLAB_PATH`: Path to your MATLAB installation
  - Default: `/Applications/MATLAB_R2024a.app`
  - Set in Claude Desktop config or when running directly

## Troubleshooting

1. **MATLAB Engine Installation Fails**
   - Verify MATLAB_PATH is correct
   - Try installing engine manually:
     ```bash
     cd $MATLAB_PATH/extern/engines/python
     python setup.py install
     ```

2. **Python Version Issues**
   - Make sure you're using Python 3.11
   - Check with: `python --version`
   - Use `uv python pin 3.11` if needed

3. **Script Execution Errors**
   - Check the `matlab_scripts` directory exists
   - Verify script syntax is valid
   - Look for error messages in MATLAB output

## Updates and Maintenance

- Keep your MATLAB installation updated
- Update Python packages as needed: `uv pip install --upgrade mcp[cli]`
- Check MATLAB engine compatibility when updating Python
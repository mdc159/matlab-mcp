import os
from pathlib import Path
import base64
import subprocess
import sys
from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP, Image, Context

# Get MATLAB path from environment variable with default fallback
MATLAB_PATH = os.getenv('MATLAB_PATH', '/Applications/MATLAB_R2024a.app')

# Initialize FastMCP server with dependencies
mcp = FastMCP(
    "MATLAB",
    dependencies=[
        "mcp[cli]"
    ]
)

def ensure_matlab_engine():
    """Ensure MATLAB engine is installed for the current Python environment."""
    try:
        import matlab.engine
        return True
    except ImportError:
        if not os.path.exists(MATLAB_PATH):
            raise RuntimeError(
                f"MATLAB installation not found at {MATLAB_PATH}. "
                "Please set MATLAB_PATH environment variable to your MATLAB installation directory."
            )
        
        # Try to install MATLAB engine
        engine_setup = Path(MATLAB_PATH) / "extern/engines/python/setup.py"
        if not engine_setup.exists():
            raise RuntimeError(
                f"MATLAB Python engine setup not found at {engine_setup}. "
                "Please verify your MATLAB installation."
            )
        
        print(f"Installing MATLAB engine from {engine_setup}...", file=sys.stderr)
        try:
            subprocess.run(
                [sys.executable, str(engine_setup), "install"],
                check=True,
                capture_output=True,
                text=True
            )
            print("MATLAB engine installed successfully.", file=sys.stderr)
            import matlab.engine
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to install MATLAB engine: {e.stderr}\n"
                "Please try installing manually or check your MATLAB installation."
            )

# Try to initialize MATLAB engine
ensure_matlab_engine()
import matlab.engine
eng = matlab.engine.start_matlab()

# Create a directory for MATLAB scripts if it doesn't exist
MATLAB_DIR = Path("matlab_scripts")
MATLAB_DIR.mkdir(exist_ok=True)

@mcp.tool()
def create_matlab_script(script_name: str, code: str) -> str:
    """Create a new MATLAB script file.
    
    Args:
        script_name: Name of the script (without .m extension)
        code: MATLAB code to save
    
    Returns:
        Path to the created script
    """
    if not script_name.isidentifier():
        raise ValueError("Script name must be a valid MATLAB identifier")
    
    script_path = MATLAB_DIR / f"{script_name}.m"
    with open(script_path, 'w') as f:
        f.write(code)
    
    return str(script_path)

@mcp.tool()
def create_matlab_function(function_name: str, code: str) -> str:
    """Create a new MATLAB function file.
    
    Args:
        function_name: Name of the function (without .m extension)
        code: MATLAB function code including function definition
    
    Returns:
        Path to the created function file
    """
    if not function_name.isidentifier():
        raise ValueError("Function name must be a valid MATLAB identifier")
    
    # Verify code starts with function definition
    if not code.strip().startswith('function'):
        raise ValueError("Code must start with function definition")
    
    function_path = MATLAB_DIR / f"{function_name}.m"
    with open(function_path, 'w') as f:
        f.write(code)
    
    return str(function_path)

@mcp.tool()
def execute_matlab_script(script_name: str, args: Optional[Dict[str, Any]] = None) -> dict:
    """Execute a MATLAB script and return results.
    
    Args:
        script_name: Name of the script (without .m extension)
        args: Optional dictionary of arguments to pass to the script
    
    Returns:
        Dictionary containing:
        - output: Text output from MATLAB
        - figures: List of figures generated (if any)
        - workspace: Variables in MATLAB workspace after execution
    """
    script_path = MATLAB_DIR / f"{script_name}.m"
    if not script_path.exists():
        raise FileNotFoundError(f"Script {script_name}.m not found")

    # Add script directory to MATLAB path
    eng.addpath(str(MATLAB_DIR))
    
    # Clear previous figures
    eng.close('all', nargout=0)
    
    # Execute the script
    result = {}
    try:
        if args:
            # Convert Python types to MATLAB types
            matlab_args = {k: matlab.double([v]) if isinstance(v, (int, float)) else v 
                         for k, v in args.items()}
            eng.workspace['args'] = matlab_args
            
        output = eng.eval(script_name, nargout=0)
        result['output'] = str(output) if output else ""
        
        # Capture figures if any were generated
        figures = []
        fig_handles = eng.eval('get(groot, "Children")', nargout=1)
        if fig_handles:
            for i, fig in enumerate(fig_handles):
                # Save figure to temporary file
                temp_file = f"temp_fig_{i}.png"
                eng.eval(f"saveas(figure({i+1}), '{temp_file}')", nargout=0)
                
                # Read the file and convert to base64
                with open(temp_file, 'rb') as f:
                    img_data = f.read()
                figures.append(Image(data=img_data, format='png'))
                
                # Clean up temp file
                os.remove(temp_file)
        
        result['figures'] = figures
        
        # Get workspace variables
        workspace = {}
        var_names = eng.eval('who', nargout=1)
        for var in var_names:
            if var != 'args':  # Skip the args we passed in
                val = eng.workspace[var]
                workspace[var] = str(val)
        result['workspace'] = workspace
        
    except Exception as e:
        raise RuntimeError(f"MATLAB execution error: {str(e)}")
        
    return result

@mcp.tool()
def call_matlab_function(function_name: str, *args: Any) -> dict:
    """Call a MATLAB function with arguments.
    
    Args:
        function_name: Name of the function (without .m extension)
        *args: Arguments to pass to the function
    
    Returns:
        Dictionary containing:
        - output: Function return value(s)
        - figures: List of figures generated (if any)
    """
    function_path = MATLAB_DIR / f"{function_name}.m"
    if not function_path.exists():
        raise FileNotFoundError(f"Function {function_name}.m not found")

    # Add function directory to MATLAB path
    eng.addpath(str(MATLAB_DIR))
    
    # Clear previous figures
    eng.close('all', nargout=0)
    
    # Convert Python arguments to MATLAB types
    matlab_args = []
    for arg in args:
        if isinstance(arg, (int, float)):
            matlab_args.append(matlab.double([arg]))
        elif isinstance(arg, list):
            matlab_args.append(matlab.double(arg))
        else:
            matlab_args.append(arg)
    
    result = {}
    try:
        # Call the function
        output = getattr(eng, function_name)(*matlab_args)
        if isinstance(output, matlab.double):
            result['output'] = output.tolist()
        else:
            result['output'] = str(output)
        
        # Capture figures if any were generated
        figures = []
        fig_handles = eng.eval('get(groot, "Children")', nargout=1)
        if fig_handles:
            for i, fig in enumerate(fig_handles):
                # Save figure to temporary file
                temp_file = f"temp_fig_{i}.png"
                eng.eval(f"saveas(figure({i+1}), '{temp_file}')", nargout=0)
                
                # Read the file and convert to base64
                with open(temp_file, 'rb') as f:
                    img_data = f.read()
                figures.append(Image(data=img_data, format='png'))
                
                # Clean up temp file
                os.remove(temp_file)
        
        result['figures'] = figures
        
    except Exception as e:
        raise RuntimeError(f"MATLAB execution error: {str(e)}")
        
    return result

@mcp.resource("matlab://scripts/{script_name}")
def get_script_content(script_name: str) -> str:
    """Get the content of a MATLAB script.
    
    Args:
        script_name: Name of the script (without .m extension)
    
    Returns:
        Content of the MATLAB script
    """
    script_path = MATLAB_DIR / f"{script_name}.m"
    if not script_path.exists():
        raise FileNotFoundError(f"Script {script_name}.m not found")
    
    with open(script_path) as f:
        return f.read()

if __name__ == "__main__":
    mcp.run(transport='stdio')

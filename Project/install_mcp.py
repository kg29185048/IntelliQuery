import os
import sys
import json
import platform
from pathlib import Path

def get_claude_config_path():
    """Determines the correct path for the Claude config based on the OS."""
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            print("❌ Error: Could not find APPDATA environment variable.")
            sys.exit(1)
        return Path(appdata) / "Claude" / "claude_desktop_config.json"
    elif system == "Darwin": # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:
        print("❌ Error: Unsupported OS. Claude Desktop currently supports Windows and macOS.")
        sys.exit(1)

def get_python_path():
    """Finds the absolute path to the Python executable in the virtual environment."""
    current_dir = Path.cwd()
    system = platform.system()
    
    if system == "Windows":
        venv_python = current_dir / "venv" / "Scripts" / "python.exe"
    else:
        venv_python = current_dir / "venv" / "bin" / "python"
        
    if not venv_python.exists():
        print(f"⚠️ Warning: Could not find virtual environment at {venv_python}")
        print("Make sure you have created a 'venv' folder in this directory.")
        # Fallback to the system Python currently running the script
        return sys.executable 
        
    return str(venv_python)

def main():
    print("==================================================")
    print("🔌 IntelliQuery MCP Setup (Groq Powered)")
    print("==================================================\n")
    
    # 1. Gather User Inputs
    print("Please provide your credentials (these are saved locally only):")
    api_key = input("Groq API Key: ").strip()
    mongo_uri = input("MongoDB Atlas URI: ").strip()
    
    if not api_key or not mongo_uri:
        print("\n❌ Error: Both API Key and MongoDB URI are required.")
        sys.exit(1)

    # 2. Resolve Paths
    config_path = get_claude_config_path()
    python_exec = get_python_path()
    mcp_server_script = str(Path.cwd() / "mcp_server.py")

    # 3. Build the Configuration Block
    mcp_config = {
        "command": python_exec,
        "args": [mcp_server_script],
        "env": {
            "GROQ_API_KEY": api_key,
            "MONGO_URI": mongo_uri
        }
    }

    # 4. Load, Update, and Save the JSON
    # Create the directory if Claude was just installed and hasn't made it yet
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    config_data = {}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except json.JSONDecodeError:
            print("\n⚠️ Warning: Existing Claude config is corrupted. Starting fresh.")
            config_data = {}

    # Ensure the mcpServers dictionary exists
    if "mcpServers" not in config_data:
        config_data["mcpServers"] = {}

    # Inject our server
    config_data["mcpServers"]["intelliquery-agent"] = mcp_config

    # Write it back to the file safely
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    # 5. Success Message
    print("\n✅ Success! IntelliQuery has been added to Claude Desktop.")
    print(f"Config saved to: {config_path}")
    print("\nPlease completely close and restart Claude Desktop to see the new tool.")

if __name__ == "__main__":
    main()
import os
import sys
import json
import platform
import glob
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent


def get_claude_config_paths():
    """Determines the Claude config path(s) based on the OS and install type."""
    system = platform.system()
    if system == "Windows":
        candidates = []

        appdata = os.environ.get("APPDATA")
        if appdata:
            candidates.append(Path(appdata) / "Claude" / "claude_desktop_config.json")

        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            candidates.append(Path(localappdata) / "Claude" / "claude_desktop_config.json")
            package_matches = glob.glob(str(Path(localappdata) / "Packages" / "Claude_*" / "LocalCache" / "Roaming" / "Claude" / "claude_desktop_config.json"))
            for match in package_matches:
                candidates.append(Path(match))

        # Remove duplicates while preserving order
        seen = set()
        unique_paths = []
        for path in candidates:
            if str(path) not in seen:
                seen.add(str(path))
                unique_paths.append(path)
        return unique_paths

    elif system == "Darwin": # macOS
        return [Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"]
    else:
        print("❌ Error: Unsupported OS. Claude Desktop currently supports Windows and macOS.")
        sys.exit(1)

def get_python_path(project_dir: Path):
    """Finds the absolute path to the Python executable in the virtual environment."""
    system = platform.system()
    
    if system == "Windows":
        venv_python = project_dir / "venv" / "Scripts" / "python.exe"
    else:
        venv_python = project_dir / "venv" / "bin" / "python"
        
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
    config_paths = get_claude_config_paths()
    if not config_paths:
        print("❌ Error: Could not determine any Claude config path.")
        sys.exit(1)

    python_exec = get_python_path(PROJECT_DIR)
    mcp_server_script = str(PROJECT_DIR / "mcp_server.py")

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
    for config_path in config_paths:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_data = {}
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except json.JSONDecodeError:
                print(f"\n⚠️ Warning: Existing Claude config at {config_path} is corrupted. Starting fresh.")
                config_data = {}

        # Ensure the mcpServers dictionary exists
        if "mcpServers" not in config_data:
            config_data["mcpServers"] = {}

        # Inject our server
        config_data["mcpServers"]["intelliquery-agent"] = mcp_config

        # Write it back to the file safely
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

        print(f"✅ Updated: {config_path}")

    # 5. Success Message
    print("\n✅ Success! IntelliQuery has been added to Claude Desktop.")
    print("Please completely close and restart Claude Desktop to see the new tool.")

if __name__ == "__main__":
    main()
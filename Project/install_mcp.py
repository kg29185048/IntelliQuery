"""
IntelliQuery MCP Setup — Registers the remote MCP server in Claude Desktop.

This script writes a URL-based config (with JWT auth header) into
Claude Desktop's configuration file. No local Python process is spawned;
Claude connects to your deployed server over HTTP/SSE.

Usage:
    python install_mcp.py
"""

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
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:
        print("❌ Error: Unsupported OS. Claude Desktop currently supports Windows and macOS.")
        sys.exit(1)


def main():
    print("==================================================")
    print("🔌 IntelliQuery MCP Setup (Remote Server)")
    print("==================================================\n")

    # 1. Gather inputs
    default_url = "https://intelliquery.onrender.com"
    print(f"Server URL (press Enter for default: {default_url}):")
    server_url = input("  > ").strip()
    if not server_url:
        server_url = default_url

    # Remove trailing slash
    server_url = server_url.rstrip("/")

    print()
    print("To get your MCP token:")
    print("  1. Log in to the IntelliQuery web app")
    print("  2. Go to Settings → MCP Token, or")
    print(f"  3. Call POST {server_url}/mcp-token with your login JWT")
    print()
    mcp_token = input("MCP Token: ").strip()

    if not mcp_token:
        print("\n❌ Error: MCP token is required.")
        sys.exit(1)

    # 2. Build the config
    config_path = get_claude_config_path()

    mcp_config = {
        "url": f"{server_url}/mcp/sse",
        "headers": {
            "Authorization": f"Bearer {mcp_token}"
        }
    }

    # 3. Load, merge, and save
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config_data = {}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except json.JSONDecodeError:
            print("\n⚠️ Warning: Existing Claude config is corrupted. Starting fresh.")
            config_data = {}

    if "mcpServers" not in config_data:
        config_data["mcpServers"] = {}

    config_data["mcpServers"]["intelliquery-agent"] = mcp_config

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    # 4. Success
    print("\n✅ Success! IntelliQuery has been added to Claude Desktop.")
    print(f"   Config saved to: {config_path}")
    print(f"   Server: {server_url}/mcp/sse")
    print(f"   Auth: JWT token (expires in 30 days)")
    print("\n📋 Please completely close and restart Claude Desktop to see the new tool.")
    print("\n💡 Claude will have two tools:")
    print("   • list_workspaces — discover your databases")
    print("   • ask_database    — query any workspace by natural language")


if __name__ == "__main__":
    main()
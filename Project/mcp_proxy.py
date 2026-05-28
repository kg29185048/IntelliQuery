import sys
import asyncio
import json
import logging
from typing import Optional
from mcp.client.sse import sse_client

logging.basicConfig(level=logging.ERROR)

async def proxy(url: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # We must ensure stdout and stdin are not buffered
    # and handle UTF-8 properly
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')
        
    try:
        async with sse_client(url, headers=headers) as (read_stream, write_stream):
            # Task to read from SSE and write to stdout
            async def read_sse():
                try:
                    async for message in read_stream:
                        print(message.model_dump_json(exclude_none=True), flush=True)
                except Exception as e:
                    print(f"SSE Read Error: {e}", file=sys.stderr)
                    sys.exit(1)

            # Task to read from stdin and write to SSE
            async def write_sse():
                loop = asyncio.get_running_loop()
                while True:
                    line = await loop.run_in_executor(None, sys.stdin.readline)
                    if not line:
                        break
                    try:
                        # Ensure it's valid JSON before sending
                        msg_data = json.loads(line)
                        # We need to construct the appropriate MCP message model.
                        # Since we don't want to reinvent parsing, we can just send the raw dict 
                        # but wait, write_stream takes MCP Message objects!
                        from mcp.types import JSONRPCMessage
                        # Pydantic v2: use model_validate
                        msg = JSONRPCMessage.model_validate(msg_data)
                        await write_stream.send(msg)
                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        print(f"Stdin Write Error: {e}", file=sys.stderr)
            
            await asyncio.gather(read_sse(), write_sse())
    except BaseException as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(f"Proxy Connection Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python mcp_proxy.py <url> <token>", file=sys.stderr)
        sys.exit(1)
        
    url = sys.argv[1]
    token = sys.argv[2]
    
    # On Windows, set event loop policy to avoid ProactorEventLoop issues with stdin
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(proxy(url, token))

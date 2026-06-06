"""Deprecated stdio entrypoint.

The MCP server is no longer served over stdio. It is mounted into the FastAPI
app as a streamable-http endpoint at ``/mcp`` (see ``app/main.py``). Run the API
service and connect an MCP client to ``http://<host>:8000/mcp``.
"""
import sys

_MESSAGE = (
    "The stdio MCP entrypoint has been removed.\n"
    "MCP is now served over HTTP at /mcp by the API service.\n"
    "Start it with:  uvicorn app.main:app --host 0.0.0.0 --port 8000\n"
    "and connect an MCP client to  http://<host>:8000/mcp\n"
)

if __name__ == "__main__":
    sys.stderr.write(_MESSAGE)
    sys.exit(1)

from app.mcp.server import mcp

# Entrypoint for `python -m app.mcp` — read-only registry server over stdio.
mcp.run()

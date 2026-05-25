from fastapi import FastAPI

app = FastAPI(title="LLM Reference Registry", version="0.1.0")


@app.get("/health")
async def health():
    return {"ok": True, "data": {"status": "healthy"}}

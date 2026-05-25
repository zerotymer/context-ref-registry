from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.entities import router as entities_router
from app.exceptions import RegistryError

app = FastAPI(title="LLM Reference Registry", version="0.1.0")


@app.exception_handler(RegistryError)
async def _registry_error_handler(request: Request, exc: RegistryError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
    )


app.include_router(entities_router)


@app.get("/health")
async def health():
    return {"ok": True, "data": {"status": "healthy"}}

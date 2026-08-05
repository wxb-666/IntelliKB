from fastapi import FastAPI

app = FastAPI(
    title = "IntelliKB API",
    version = "0.1.0",
)

@app.get("/healthz", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
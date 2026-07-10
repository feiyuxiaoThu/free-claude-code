import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn


client = httpx.AsyncClient(base_url="https://opencode.ai/zen/v1", timeout=httpx.Timeout(120.0, connect=10.0))

# Cached, filtered `/v1/models` payload (only free models); populated once at startup.
free_models_payload: dict = {"object": "list", "data": []}


def _is_free(model_id: str) -> bool:
    return model_id.endswith("-free") or model_id == "big-pickle"


async def load_free_models() -> None:
    """Fetch the upstream model list once at startup and keep only free models."""
    global free_models_payload
    try:
        r = await client.get("models")
        r.raise_for_status()
        payload = r.json()
    except Exception as exc:  # noqa: BLE001 - surface but keep proxy running
        print(f"[opencode-proxy] WARN: failed to fetch upstream /v1/models: {exc}")
        return

    upstream = payload.get("data", []) if isinstance(payload, dict) else []
    free = [m for m in upstream if _is_free(m.get("id", ""))]
    payload["data"] = free
    free_models_payload = payload

    print(f"[opencode-proxy] startup: loaded {len(free)} free model(s):")
    for m in sorted(free, key=lambda x: x["id"]):
        print(f"  - {m['id']}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await load_free_models()
    yield
    await client.aclose()


app = FastAPI(lifespan=lifespan)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def proxy(request: Request, path: str):
    cleaned_path = path[3:] if path.startswith("v1/") else path
    if cleaned_path == "models" and request.method == "GET":
        return JSONResponse(content=free_models_payload, status_code=200)
    # Get request body
    body = await request.body()
    
    # Copy headers and remove Authorization
    headers = dict(request.headers)
    headers.pop("authorization", None)
    headers.pop("host", None)  # Let httpx handle Host header
    
    # Forward query parameters
    params = dict(request.query_params)
    
                
    # Fetch response status and headers
    req = client.build_request(
        method=request.method,
        url=cleaned_path,
        headers=headers,
        params=params,
        content=body
    )
    r = await client.send(req, stream=True)

    async def stream_response():
        try:
            async for chunk in r.aiter_bytes():
                yield chunk
        finally:
            await r.aclose()
    
    # Build response headers, removing transfer-encoding/content-encoding to prevent mismatch
    resp_headers = dict(r.headers)
    resp_headers.pop("transfer-encoding", None)
    resp_headers.pop("content-encoding", None)
    
    return StreamingResponse(
        stream_response(),
        status_code=r.status_code,
        headers=resp_headers
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=4000)

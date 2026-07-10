import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn

app = FastAPI()
client = httpx.AsyncClient(base_url="https://opencode.ai/zen/v1", timeout=httpx.Timeout(120.0, connect=10.0))

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def proxy(request: Request, path: str):
    cleaned_path = path[3:] if path.startswith("v1/") else path
    if cleaned_path == "models" and request.method == "GET":
        r = await client.get("models")
        data = r.json()
        if "data" in data and isinstance(data["data"], list):
            data["data"] = [
                m for m in data["data"]
                if m.get("id", "").endswith("-free") or m.get("id", "") == "big-pickle"
            ]
        return JSONResponse(content=data, status_code=r.status_code)
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

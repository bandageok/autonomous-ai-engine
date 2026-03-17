import uvicorn
from api.fastapi_server import app

if __name__ == "__main__":
    print("Starting FastAPI server on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)

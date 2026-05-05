from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="DocuMind API",
    description="Backend service for DocuMind AI Document Assistant",
    version="1.0.0"
)

# Cấu hình CORS cho phép Mobile App kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to DocuMind API",
        "status": "online",
        "version": "1.0.0"
    }

@app.post("/upload-test")
async def upload_test():
    """Endpoint giả lập để test luồng xử lý tài liệu."""
    return {
        "status": "success",
        "message": "Endpoint này sẽ nhận file và gọi DoclingProcessor trong tương lai gần."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

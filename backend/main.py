import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Sửa lỗi ModuleNotFoundError: Thêm thư mục gốc vào PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.db import init_db
from backend.app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo database (tạo bảng nếu chưa có)
    # Lưu ý: Cần cấu hình đúng DATABASE_URL trong .env hoặc config.py
    try:
        init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend service for DocuMind AI Document Assistant",
    lifespan=lifespan
)

# Cấu hình CORS
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
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "status": "online",
        "version": settings.VERSION
    }

# Import các router
from backend.app.api import notebooks, auth, documents

# Include các router
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(notebooks.router, prefix=f"{settings.API_V1_STR}/notebooks", tags=["notebooks"])
app.include_router(documents.router, prefix=settings.API_V1_STR, tags=["documents"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

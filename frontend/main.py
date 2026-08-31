import os
from pathlib import Path

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles


# ตำแหน่งไฟล์หน้าเว็บ และ URL ของเครื่อง Backend
# เมื่อนำไปใช้คนละเครื่อง สามารถเปลี่ยน BACKEND_URL ผ่าน environment variable ได้
BASE_DIR = Path(__file__).resolve().parent
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8001")

# สร้างแอป FastAPI สำหรับเครื่อง Frontend
app = FastAPI(
    title="Image Processing Frontend",
    description="หน้าเว็บ Client สำหรับส่งภาพไปยัง Image Processing Backend",
    version="1.0.0",
)
# เปิดให้ Browser เข้าถึงไฟล์ HTML, CSS และ JavaScript ในโฟลเดอร์ static
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", response_class=FileResponse)
async def index() -> FileResponse:
    # ส่งหน้าเว็บหลักให้ Client เมื่อเปิด URL ของ Frontend
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    # Endpoint สำหรับตรวจสอบสถานะของ Frontend
    return {"status": "ok", "service": "image-processing-frontend"}


@app.post("/api/process")
async def forward_image(
    file: UploadFile = File(...),
    operation: str = Form("grayscale"),
) -> Response:
    # อ่านไฟล์ที่ Browser ส่งมา แล้วเตรียมส่งต่อไปยัง Backend
    file_bytes = await file.read()
    await file.close()

    # ใช้ httpx ส่ง multipart/form-data ซึ่งประกอบด้วยไฟล์ภาพและ operation
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            backend_response = await client.post(
                f"{BACKEND_URL}/process",
                files={
                    "file": (
                        file.filename or "upload",
                        file_bytes,
                        file.content_type or "application/octet-stream",
                    )
                },
                data={"operation": operation},
            )
    except httpx.RequestError as exc:
        # แจ้ง Client ด้วยรหัส 503 เมื่อเชื่อมต่อเครื่อง Backend ไม่ได้
        raise HTTPException(
            status_code=503,
            detail="ไม่สามารถเชื่อมต่อ Backend ได้ กรุณาตรวจสอบว่า Backend กำลังทำงาน",
        ) from exc

    # ส่ง status, content type และข้อมูลภาพจาก Backend กลับไปยัง Browser
    return Response(
        content=backend_response.content,
        status_code=backend_response.status_code,
        media_type=backend_response.headers.get("content-type", "application/json"),
    )

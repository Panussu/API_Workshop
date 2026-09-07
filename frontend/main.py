"""Frontend FastAPI สำหรับเสิร์ฟหน้าเว็บและทำหน้าที่ proxy ไปยัง Backend."""

# ==================== ส่วนที่ 1: Imports และ Dependencies ====================
# รวมเครื่องมือสำหรับอ่าน configuration, เสิร์ฟไฟล์ และเรียก Backend ผ่าน HTTP

# os ใช้อ่านค่า configuration จาก environment variable
import os
# Path ใช้สร้างตำแหน่งไฟล์ static แบบที่ทำงานได้ข้ามระบบปฏิบัติการ
from pathlib import Path

# httpx เป็น HTTP client ที่ Frontend ใช้ส่งไฟล์ต่อไปยัง Backend
import httpx
# FastAPI ใช้สร้างแอป; File/Form/UploadFile ใช้รับ multipart form จาก Browser
# HTTPException ใช้แจ้งกรณี Frontend ติดต่อ Backend ไม่ได้
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
# FileResponse ใช้ส่ง index.html ส่วน Response ใช้ส่ง body/status ของ Backend ต่อ
from fastapi.responses import FileResponse, Response
# StaticFiles ทำให้ Browser ขอไฟล์ CSS และ JavaScript ในโฟลเดอร์ static ได้
from fastapi.staticfiles import StaticFiles


# ==================== ส่วนที่ 2: Configuration ====================
# ระบุตำแหน่งไฟล์หน้าเว็บและ URL ของ Backend ที่ Frontend จะเชื่อมต่อ

# หา absolute path ของโฟลเดอร์ frontend โดยอิงตำแหน่งไฟล์นี้
BASE_DIR = Path(__file__).resolve().parent
# ใช้ URL จาก environment เมื่อตั้งไว้ หรือชี้ไปพอร์ต 8001 บนเครื่องเดียวกัน
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8001")

# ==================== ส่วนที่ 3: การสร้าง FastAPI และ Static Files ====================
# สร้างแอป Frontend และเปิดให้ Browser โหลด HTML, CSS และ JavaScript

# สร้าง Frontend application; metadata จะแสดงใน /docs และ OpenAPI
app = FastAPI(
    # ชื่อ service ในเอกสาร API
    title="Image Processing Frontend",
    # คำอธิบายหน้าที่ของ service
    description="หน้าเว็บ Client สำหรับส่งภาพไปยัง Image Processing Backend",
    # เวอร์ชันของ API นี้
    version="1.0.0",
)
# URL ที่ขึ้นต้นด้วย /static จะอ่านไฟล์จาก frontend/static
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


# ==================== ส่วนที่ 4: Page และ Health Endpoints ====================
# Endpoint กลุ่มนี้ใช้ส่งหน้าเว็บและรายงานสถานะของ Frontend

# ---------- 4.1 หน้าเว็บหลัก ----------
# ผูกหน้าแรกของเว็บไซต์เข้ากับ GET /
@app.get("/", response_class=FileResponse)
async def index() -> FileResponse:
    """ส่งหน้า HTML หลักของ Workshop ให้ Browser."""

    # FileResponse อ่านไฟล์และกำหนด HTTP response ที่เหมาะสมให้
    return FileResponse(BASE_DIR / "static" / "index.html")


# ---------- 4.2 Health Check ----------
# Endpoint สำหรับระบบ monitoring ตรวจสอบว่า Frontend ยังตอบสนอง
@app.get("/health")
async def health() -> dict[str, str]:
    """คืนสถานะพื้นฐานสำหรับ health check ของ Frontend."""

    # Dictionary จะถูก FastAPI serialize เป็น JSON
    return {"status": "ok", "service": "image-processing-frontend"}


# ==================== ส่วนที่ 5: Backend Proxy Endpoint ====================
# รับไฟล์จาก Browser ส่งต่อไป Backend และนำ response เดิมกลับมาให้ Browser

# Browser ส่ง form มาที่ path นี้แทนการเรียก Backend โดยตรง
@app.post("/api/process")
async def forward_image(
    # รับ field "file" ที่จำเป็นจาก multipart/form-data
    file: UploadFile = File(...),
    # รับ operation และกำหนดค่าเริ่มต้นให้ตรงกับ Backend
    operation: str = Form("grayscale"),
) -> Response:
    """ส่งภาพและ operation ไปยัง Backend แล้วส่ง response กลับให้ Browser."""

    # อ่านไฟล์ทั้งหมดเป็น bytes เพื่อใส่ใน request ที่จะส่งต่อ
    # ขนาดไฟล์จะถูกตรวจโดย Backend แต่ข้อมูลมาถึง Frontend memory ก่อนแล้ว
    file_bytes = await file.read()
    # ปิด UploadFile เมื่ออ่านเสร็จ
    await file.close()

    # ปัญหาเครือข่ายหรือ timeout อาจเกิดขึ้นขณะติดต่อ Backend
    try:
        # ใช้ AsyncClient เพื่อไม่บล็อก event loop และหยุดรอเมื่อเกิน 30 วินาที
        async with httpx.AsyncClient(timeout=30.0) as client:
            # ส่ง multipart/form-data ไปยัง endpoint /process ของ Backend
            backend_response = await client.post(
                # รองรับการเปลี่ยน host ผ่าน BACKEND_URL โดยไม่แก้ source code
                f"{BACKEND_URL}/process",
                files={
                    # tuple มีรูปแบบ (ชื่อไฟล์, bytes, MIME type)
                    "file": (
                        # ใช้ชื่อเดิม หรือชื่อสำรองถ้า Browser ไม่ได้ให้ชื่อมา
                        file.filename or "upload",
                        # เนื้อหาไฟล์จริง
                        file_bytes,
                        # ใช้ MIME type เดิม หรือชนิด binary ทั่วไปเป็น fallback
                        file.content_type or "application/octet-stream",
                    )
                },
                # form field อื่นนอกเหนือจากไฟล์
                data={"operation": operation},
            )
    # RequestError ครอบคลุม connection error, DNS error และ timeout
    except httpx.RequestError as exc:
        # 503 สื่อว่า service ปลายทางไม่พร้อมใช้งานชั่วคราว
        # เชื่อม exception ต้นเหตุไว้เพื่อให้ traceback บอกสาเหตุด้าน network ได้
        raise HTTPException(
            status_code=503,
            detail="ไม่สามารถเชื่อมต่อ Backend ได้ กรุณาตรวจสอบว่า Backend กำลังทำงาน",
        ) from exc

    # ทำตัวเป็น proxy โดยรักษา body, status code และ content type จาก Backend
    return Response(
        # อาจเป็น bytes ของ PNG หรือ JSON ที่อธิบาย error
        content=backend_response.content,
        # เช่น 200, 400, 413 หรือ 415
        status_code=backend_response.status_code,
        # ใช้ Content-Type ต้นทาง หรือ JSON เป็นค่าเริ่มต้นหาก header หายไป
        media_type=backend_response.headers.get("content-type", "application/json"),
    )

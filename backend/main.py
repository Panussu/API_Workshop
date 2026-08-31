from io import BytesIO

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError


# กำหนดข้อจำกัดของไฟล์และรายการวิธีประมวลผลที่ Backend รองรับ
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
OPERATIONS = {"grayscale", "blur", "edge", "invert"}

# สร้างแอป FastAPI สำหรับเครื่อง Backend
app = FastAPI(
    title="Image Processing Backend",
    description="รับไฟล์ภาพ ประมวลผล และส่งภาพผลลัพธ์กลับไปให้ Client",
    version="1.0.0",
)

# อนุญาตให้หน้าเว็บ Frontend ที่รันในเครื่องเดียวกันเรียกใช้ API ได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def process_image(image: Image.Image, operation: str) -> Image.Image:
    """ประมวลผลภาพตาม operation ที่เลือก และคืนภาพในรูปแบบสี RGB"""
    # แปลงภาพเป็น RGB ก่อน เพื่อให้ทุก operation ทำงานกับโหมดสีเดียวกัน
    rgb_image = image.convert("RGB")

    # เลือกวิธีประมวลผลจากค่าที่ Client ส่งมา
    if operation == "grayscale":
        return ImageOps.grayscale(rgb_image).convert("RGB")
    if operation == "blur":
        return rgb_image.filter(ImageFilter.GaussianBlur(radius=4))
    if operation == "edge":
        return rgb_image.filter(ImageFilter.FIND_EDGES)
    if operation == "invert":
        return ImageOps.invert(rgb_image)

    raise ValueError(f"Unsupported operation: {operation}")


@app.get("/health")
async def health() -> dict[str, str]:
    # Endpoint นี้ใช้ตรวจสอบว่า Backend เปิดทำงานอยู่หรือไม่
    return {"status": "ok", "service": "image-processing-backend"}


@app.post(
    "/process",
    response_class=StreamingResponse,
    responses={200: {"content": {"image/png": {}}}},
)
async def process_uploaded_image(
    file: UploadFile = File(...),
    operation: str = Form("grayscale"),
) -> StreamingResponse:
    # ตรวจสอบชนิดไฟล์จาก Content-Type ก่อนอ่านข้อมูลภาพ
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="รองรับเฉพาะไฟล์ JPEG, PNG และ WebP",
        )
    if operation not in OPERATIONS:
        raise HTTPException(status_code=400, detail="ไม่รู้จักรูปแบบการประมวลผล")

    # อ่านเกินขนาดสูงสุด 1 byte เพื่อใช้ตรวจว่าไฟล์ใหญ่เกิน 10 MB หรือไม่
    file_bytes = await file.read(MAX_FILE_SIZE + 1)
    await file.close()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="ไฟล์ภาพว่างเปล่า")
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="ไฟล์ภาพต้องมีขนาดไม่เกิน 10 MB")

    # เปิดภาพจากข้อมูลในหน่วยความจำ แล้วเรียกฟังก์ชันประมวลผล
    try:
        with Image.open(BytesIO(file_bytes)) as source_image:
            source_image.load()
            result_image = process_image(source_image, operation)
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=400, detail="ไม่สามารถอ่านหรือประมวลผลภาพนี้ได้")

    # บันทึกภาพผลลัพธ์เป็น PNG ลงในหน่วยความจำ โดยไม่สร้างไฟล์ชั่วคราวบน Server
    output = BytesIO()
    result_image.save(output, format="PNG")
    output.seek(0)

    # ส่งข้อมูลภาพ PNG กลับไปยัง Frontend ด้วย HTTP response
    return StreamingResponse(
        output,
        media_type="image/png",
        headers={
            "Content-Disposition": 'inline; filename="processed-image.png"',
            "X-Image-Operation": operation,
        },
    )

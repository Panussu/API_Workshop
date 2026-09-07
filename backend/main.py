"""Backend API สำหรับตรวจสอบ ประมวลผล และส่งภาพ PNG กลับไปยัง Client."""

# ==============================================================================
# GROUP 1: IMPORTS & DEPENDENCIES
# ==============================================================================

# BytesIO ทำให้ข้อมูล bytes ใช้งานเหมือนไฟล์ที่อยู่ในหน่วยความจำ
# จึงไม่จำเป็นต้องสร้างไฟล์ชั่วคราวบนดิสก์ระหว่างประมวลผลภาพ
from io import BytesIO

# FastAPI ใช้สร้างแอปและ route ส่วน File/Form ใช้อ่าน multipart/form-data
# HTTPException ใช้ตอบข้อผิดพลาดเป็น HTTP status และ UploadFile แทนไฟล์อัปโหลด
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

# CORSMiddleware กำหนดว่าเว็บไซต์จาก origin ใดเรียก API ผ่าน Browser ได้
from fastapi.middleware.cors import CORSMiddleware

# StreamingResponse ส่งข้อมูลภาพจาก buffer กลับไปโดยไม่ต้องบันทึกเป็นไฟล์จริง
from fastapi.responses import StreamingResponse

# Pillow ให้ชนิด Image, filter สำหรับเบลอ/หาขอบ, utility สำหรับเทา/กลับสี
# และ exception สำหรับกรณีข้อมูลที่รับมาไม่ใช่ไฟล์ภาพที่ Pillow รู้จัก
from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError


# ==============================================================================
# GROUP 2: CONFIGURATION & CONSTANTS
# ==============================================================================

# จำกัดข้อมูลที่อ่านไว้ที่ 10 MiB (10 × 1024 × 1024 ไบต์)
MAX_FILE_SIZE = 10 * 1024 * 1024

# MIME type ที่ยอมรับในส่วน file ของ multipart request
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

# ชื่อ operation ที่ Client สามารถขอให้ Backend ทำได้
OPERATIONS = {"grayscale", "blur", "edge", "invert"}


# ==============================================================================
# GROUP 3: FASTAPI APPLICATION SETUP & CORS MIDDLEWARE
# ==============================================================================

# สร้าง FastAPI application; metadata ชุดนี้จะแสดงในหน้า /docs และ OpenAPI
app = FastAPI(
    # ชื่อ service ในเอกสาร API
    title="Image Processing Backend",
    # คำอธิบายหน้าที่ของ service
    description="รับไฟล์ภาพ ประมวลผล และส่งภาพผลลัพธ์กลับไปให้ Client",
    # เวอร์ชัน API ไม่ใช่เวอร์ชันของ FastAPI
    version="1.0.0",
)

# เพิ่ม CORS middleware เผื่อ JavaScript จาก Frontend เรียก Backend โดยตรง
app.add_middleware(
    # เลือก middleware ที่จะติดตั้งใน request/response pipeline
    CORSMiddleware,
    # อนุญาตเฉพาะหน้าเว็บที่เปิดจาก Frontend พอร์ต 8000 บนเครื่องเดียวกัน
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    # อนุญาต credential เช่น cookie ใน cross-origin request
    allow_credentials=True,
    # Cross-origin request ใช้ได้เฉพาะ GET และ POST
    allow_methods=["GET", "POST"],
    # Client สามารถส่ง request header ชื่อใดก็ได้
    allow_headers=["*"],
)


# ==============================================================================
# GROUP 4: CORE IMAGE PROCESSING LOGIC
# ==============================================================================

def process_image(image: Image.Image, operation: str) -> Image.Image:
    """ประมวลผลภาพตาม operation ที่เลือก แล้วคืน Pillow Image โหมด RGB."""

    # ทำให้ทุก operation รับข้อมูลสีสาม channel เหมือนกัน
    # หากภาพต้นฉบับมี alpha/transparency ข้อมูลส่วนนั้นจะถูกตัดออกที่ขั้นตอนนี้
    rgb_image = image.convert("RGB")

    # ภาพขาวดำของ Pillow เป็นโหมด L จึงแปลงกลับเป็น RGB ก่อนคืนค่า
    if operation == "grayscale":
        return ImageOps.grayscale(rgb_image).convert("RGB")

    # Gaussian blur ทำให้ภาพนุ่มลง โดย radius=4 กำหนดความแรงของการเบลอ
    if operation == "blur":
        return rgb_image.filter(ImageFilter.GaussianBlur(radius=4))

    # FIND_EDGES เป็น convolution filter สำเร็จรูปสำหรับเน้นบริเวณขอบ
    if operation == "edge":
        return rgb_image.filter(ImageFilter.FIND_EDGES)

    # invert เปลี่ยนค่าของแต่ละ channel จาก x เป็น 255-x
    if operation == "invert":
        return ImageOps.invert(rgb_image)

    # เป็น guard สำหรับกรณีมีการเรียกฟังก์ชันนี้จากที่อื่นด้วยค่าที่ไม่รองรับ
    raise ValueError(f"Unsupported operation: {operation}")


# ==============================================================================
# GROUP 5: API ENDPOINTS (ROUTES)
# ==============================================================================

# ผูกฟังก์ชัน health กับคำขอ GET /health
@app.get("/health")
async def health() -> dict[str, str]:
    """คืนสถานะพื้นฐานสำหรับ health check ของ Backend."""

    # FastAPI จะแปลง dictionary นี้เป็น JSON response โดยอัตโนมัติ
    return {"status": "ok", "service": "image-processing-backend"}


# ผูกฟังก์ชันด้านล่างกับคำขอ POST /process
@app.post(
    # URL path สำหรับรับภาพ
    "/process",
    # ระบุชนิด response หลักว่าเป็นข้อมูลแบบ stream
    response_class=StreamingResponse,
    # เพิ่ม media type image/png ลงในเอกสาร OpenAPI สำหรับสถานะ 200
    responses={200: {"content": {"image/png": {}}}},
)
async def process_uploaded_image(
    # File(...) ทำให้ field "file" เป็นค่าบังคับใน multipart/form-data
    file: UploadFile = File(...),
    # Form(...) อ่าน field "operation" และใช้ grayscale เมื่อ Client ไม่ส่งมา
    operation: str = Form("grayscale"),
) -> StreamingResponse:
    """ตรวจสอบไฟล์ ใช้ operation ที่ร้องขอ และตอบกลับเป็นภาพ PNG."""

    # ตรวจ MIME type เบื้องต้นก่อนอ่านข้อมูลขนาดใหญ่
    # ค่านี้มาจาก Client จึงยังต้องใช้ Pillow ตรวจเนื้อหาจริงในภายหลังด้วย
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            # 415 หมายถึง Server ไม่รองรับ media type ที่ส่งมา
            status_code=415,
            detail="รองรับเฉพาะไฟล์ JPEG, PNG และ WebP",
        )

    # ปฏิเสธชื่อ operation ที่ไม่อยู่ในรายการที่ Backend รองรับ
    if operation not in OPERATIONS:
        raise HTTPException(status_code=400, detail="ไม่รู้จักรูปแบบการประมวลผล")

    # อ่านเกินเพดาน 1 ไบต์เพื่อแยกไฟล์ที่ขนาดพอดีออกจากไฟล์ที่ใหญ่เกินกำหนด
    file_bytes = await file.read(MAX_FILE_SIZE + 1)
    # ปิด UploadFile ทันทีเมื่อไม่ต้องใช้อีก เพื่อคืน file handle/temporary storage
    await file.close()

    # ไฟล์ที่มีศูนย์ไบต์ไม่สามารถนำไปเปิดเป็นภาพได้
    if not file_bytes:
        raise HTTPException(status_code=400, detail="ไฟล์ภาพว่างเปล่า")

    # ถ้าอ่านได้ไบต์ที่เกินมา แสดงว่าไฟล์มีขนาดมากกว่า 10 MiB
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="ไฟล์ภาพต้องมีขนาดไม่เกิน 10 MB")

    # การเปิดและถอดรหัสไฟล์ภาพอาจล้มเหลว จึงครอบด้วย try/except
    try:
        # BytesIO เปลี่ยน bytes ให้ Pillow อ่านผ่าน file-like interface ได้
        # with จะปิด source_image ให้อัตโนมัติเมื่อจบบล็อก
        with Image.open(BytesIO(file_bytes)) as source_image:
            # Image.open โหลดแบบ lazy; load() บังคับถอดรหัส pixel ทั้งหมดตอนนี้
            source_image.load()
            # สร้างภาพผลลัพธ์ขณะที่ข้อมูลภาพต้นฉบับยังเปิดใช้งานอยู่
            result_image = process_image(source_image, operation)
    # รวมกรณีไม่รู้จักรูปแบบภาพ, ภาพเสีย, decoder ล้มเหลว และ operation ผิด
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=400, detail="ไม่สามารถอ่านหรือประมวลผลภาพนี้ได้")

    # สร้าง buffer สำหรับเก็บไฟล์ผลลัพธ์ใน RAM
    output = BytesIO()
    # เข้ารหัส Pillow Image เป็นรูปแบบ PNG แล้วเขียนลง buffer
    result_image.save(output, format="PNG")
    # หลัง save ตำแหน่งอยู่ท้าย buffer จึงต้องย้อนกลับไปก่อน byte แรกเพื่ออ่าน
    output.seek(0)

    # ส่ง buffer กลับในรูป StreamingResponse โดยไม่สร้างไฟล์บน Server
    return StreamingResponse(
        # แหล่งข้อมูลที่ response จะอ่านและส่งออก
        output,
        # Content-Type ที่บอก Client ว่า body เป็น PNG
        media_type="image/png",
        headers={
            # inline แนะนำให้แสดงในหน้าเว็บ และกำหนดชื่อไฟล์เริ่มต้น
            "Content-Disposition": 'inline; filename="processed-image.png"',
            # custom header ระบุ operation ที่ใช้สร้างผลลัพธ์
            "X-Image-Operation": operation,
        },
    )

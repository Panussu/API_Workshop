from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app


client = TestClient(app)


def create_test_image() -> bytes:
    # สร้างภาพ PNG สีแดงขนาดเล็กในหน่วยความจำสำหรับใช้ทดสอบ API
    output = BytesIO()
    Image.new("RGB", (12, 8), color=(255, 0, 0)).save(output, format="PNG")
    return output.getvalue()


def test_health() -> None:
    # ตรวจว่า health endpoint ตอบกลับว่าระบบพร้อมทำงาน
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_process_grayscale_image() -> None:
    # ส่งภาพเข้า API และตรวจว่าภาพผลลัพธ์มีค่า R, G, B เท่ากัน
    response = client.post(
        "/process",
        files={"file": ("sample.png", create_test_image(), "image/png")},
        data={"operation": "grayscale"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    with Image.open(BytesIO(response.content)) as result:
        assert result.size == (12, 8)
        red, green, blue = result.getpixel((0, 0))
        assert red == green == blue


def test_rejects_non_image_file() -> None:
    # ไฟล์ข้อความต้องถูกปฏิเสธด้วย HTTP 415 Unsupported Media Type
    response = client.post(
        "/process",
        files={"file": ("notes.txt", b"not an image", "text/plain")},
        data={"operation": "grayscale"},
    )
    assert response.status_code == 415


def test_rejects_unknown_operation() -> None:
    # operation ที่ไม่มีในรายการต้องถูกปฏิเสธด้วย HTTP 400
    response = client.post(
        "/process",
        files={"file": ("sample.png", create_test_image(), "image/png")},
        data={"operation": "unknown"},
    )
    assert response.status_code == 400

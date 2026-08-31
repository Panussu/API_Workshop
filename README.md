# Image Processing Workshop with FastAPI

โปรเจกต์นี้แบ่งเป็น 2 Service ซึ่งสามารถรันคนละเครื่องได้

- **Frontend** รับไฟล์จากผู้ใช้ แสดงภาพต้นฉบับ และส่งคำขอไปยัง Backend
- **Backend** รับไฟล์ภาพ ประมวลผลด้วย Pillow และส่งภาพ PNG กลับมา

รองรับการประมวลผล 4 แบบ: Grayscale, Blur, Edge Detection และ Invert

## การไหลของข้อมูล

```text
Web Browser -> Frontend FastAPI (port 8000)
            -> Backend FastAPI  (port 8001)
            -> Frontend -> Web Browser
```

## ติดตั้ง

ต้องใช้ Python 3.10 หรือใหม่กว่า เปิด PowerShell ที่โฟลเดอร์โปรเจกต์แล้วรัน

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## รันบนเครื่องเดียวกัน

เปิด PowerShell หน้าต่างที่ 1 สำหรับ Backend

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

เปิด PowerShell หน้าต่างที่ 2 สำหรับ Frontend

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn frontend.main:app --host 0.0.0.0 --port 8000
```

จากนั้นเปิด <http://127.0.0.1:8000>

เอกสาร API ของ Backend อยู่ที่ <http://127.0.0.1:8001/docs>

## รัน Frontend และ Backend คนละเครื่อง

1. รัน Backend ด้วย `--host 0.0.0.0` บนเครื่อง Server และเปิด TCP port 8001 ใน Firewall
2. หา IP ของเครื่อง Backend เช่น `192.168.1.20`
3. ก่อนรัน Frontend ให้กำหนด URL ของ Backend

```powershell
$env:BACKEND_URL = "http://192.168.1.20:8001"
python -m uvicorn frontend.main:app --host 0.0.0.0 --port 8000
```

4. Client เปิด `http://<FRONTEND-IP>:8000` ผ่าน Browser

## ทดสอบ

```powershell
python -m pytest -q
```

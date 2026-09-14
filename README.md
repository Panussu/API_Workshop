# Image Processing Workshop with FastAPI

โปรเจกต์นี้ประกอบด้วยหน้าเว็บแบบ Static และ Backend API ซึ่งสามารถอยู่คนละเครื่องได้

- **Frontend** เป็น HTML/CSS/JavaScript ล้วน รับไฟล์จากผู้ใช้และเรียก Backend โดยตรง
- **Backend** รับไฟล์ภาพ ประมวลผลด้วย Pillow และส่งภาพ PNG กลับมา

รองรับการประมวลผล 4 แบบ: Grayscale, Blur, Edge Detection และ Invert

## การไหลของข้อมูล

```text
frontend/static/index.html -> Backend FastAPI (port 8001)
                           -> Web Browser
```

## ติดตั้ง

ต้องใช้ Python 3.10 หรือใหม่กว่า เปิด PowerShell ที่โฟลเดอร์โปรเจกต์แล้วรัน

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## รัน Backend

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

จากนั้นเปิดไฟล์ `frontend/static/index.html` ด้วย Browser ไม่ต้องรัน Python สำหรับ Frontend
โดย URL ของ Backend กำหนดไว้ใน `frontend/static/app.js`

เอกสาร API ของ Backend อยู่ที่ <http://127.0.0.1:8001/docs>

## ใช้ Frontend และ Backend คนละเครื่อง

1. รัน Backend ด้วย `--host 0.0.0.0` บนเครื่อง Server และเปิด TCP port 8001 ใน Firewall
2. หา IP ของเครื่อง Backend เช่น `192.168.1.20`
3. คัดลอกโฟลเดอร์ `frontend/static` ไปยังเครื่อง Frontend
4. กำหนด `BACKEND_URL` ใน `app.js` ให้เป็น IP ของเครื่อง Backend แล้วเปิด `index.html` ด้วย Browser
5. หาก Browser ขอสิทธิ์เข้าถึงอุปกรณ์ในเครือข่ายภายใน ให้กดอนุญาต

## ทดสอบ

```powershell
python -m pytest tests -q
```

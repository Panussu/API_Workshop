// ==================== ส่วนที่ 1: DOM Element References ====================
// เลือก HTML element ที่ JavaScript ต้องอ่านค่า เปลี่ยนสถานะ และแสดงผล

// querySelector คืน element แรกที่ตรงกับ CSS selector ที่ระบุ
// script ถูกโหลดท้าย body จึงมั่นใจได้ว่า element เหล่านี้ถูกสร้างแล้ว
// form เป็นจุดที่ใช้ดักเหตุการณ์ submit
const form = document.querySelector("#upload-form");
// URL ของ Backend ถูกกำหนดภายในโค้ด จึงไม่ต้องแสดงช่องตั้งค่าบนหน้าเว็บ
const BACKEND_URL = "http://172.20.57.133:8001";
// fileInput ใช้อ่าน FileList ที่ผู้ใช้เลือก
const fileInput = document.querySelector("#image-file");
// statusText แสดงสถานะ loading, success หรือ error
const statusText = document.querySelector("#status");
// submitButton ถูก disable ระหว่างรอ response เพื่อป้องกันการส่งซ้ำ
const submitButton = document.querySelector("#submit-button");
// results คือ section ที่ซ่อนอยู่จนกว่าจะได้รับภาพสำเร็จ
const results = document.querySelector("#results");
// image element สำหรับ preview ไฟล์ต้นฉบับ
const originalImage = document.querySelector("#original-image");
// image element สำหรับ PNG ที่ผ่านการประมวลผล
const processedImage = document.querySelector("#processed-image");
// anchor ที่จะชี้ไปยัง Object URL ของผลลัพธ์เพื่อดาวน์โหลด
const downloadLink = document.querySelector("#download-link");

// ==================== ส่วนที่ 2: Object URL State ====================
// เก็บ URL ชั่วคราวของภาพรอบล่าสุด เพื่อให้คืนหน่วยความจำก่อนสร้างรอบใหม่

// เก็บ Object URL ล่าสุดไว้นอก callback เพื่อให้ยกเลิกก่อนสร้างรอบใหม่ได้
let originalUrl;
let processedUrl;

// ==================== ส่วนที่ 3: Form Submission Flow ====================
// ควบคุมตั้งแต่ตรวจไฟล์ ส่ง request รับ Blob แสดงภาพ ไปจนถึงจัดการ error

// callback นี้ทำงานเมื่อผู้ใช้ submit form เช่นกดปุ่ม "ประมวลผลภาพ"
form.addEventListener("submit", async (event) => {
  // ---------- 3.1 ป้องกันการโหลดหน้าใหม่และตรวจไฟล์ ----------
  // ยกเลิกพฤติกรรมปกติของ form ที่จะนำทาง/โหลดหน้าใหม่
  event.preventDefault();
  // FileList ใช้ index 0 เพราะ input นี้ไม่ได้เปิดให้เลือกหลายไฟล์
  const file = fileInput.files[0];
  // ป้องกันกรณี callback ถูกเรียกโดยไม่มีไฟล์ แม้ HTML จะมี required อยู่แล้ว
  if (!file) return;

  // ล็อกปุ่มจนกว่า request รอบนี้จะสิ้นสุด
  submitButton.disabled = true;
  // className เชื่อมกับสี .loading ใน CSS
  statusText.className = "loading";
  statusText.textContent = "กำลังส่งภาพไปประมวลผล...";

  // ---------- 3.2 สร้างและส่ง HTTP Request ----------
  // ครอบขั้นตอน network และแปลง response เพื่อแสดง error ที่เข้าใจง่าย
  try {
    // สร้าง multipart/form-data จาก control ทุกตัวที่มี name อยู่ใน form
    // จึงได้ field "file" และ "operation" ตรงกับ parameter ของ FastAPI
    const formData = new FormData(form);
    // ไม่กำหนด Content-Type เอง เพราะ Browser ต้องเติม multipart boundary ให้ถูกต้อง
    const response = await fetch(`${BACKEND_URL}/process`, {
      method: "POST",
      body: formData,
    });

    // fetch ไม่ throw เมื่อได้ HTTP 4xx/5xx จึงต้องตรวจ response.ok เอง
    if (!response.ok) {
      // FastAPI ส่ง error เป็น JSON; ถ้า body ไม่ใช่ JSON ให้ fallback เป็น object ว่าง
      const error = await response.json().catch(() => ({}));
      // ใช้ detail จาก Server หรือข้อความทั่วไปเมื่อไม่มีรายละเอียด
      throw new Error(error.detail || "ประมวลผลภาพไม่สำเร็จ");
    }

    // ---------- 3.3 แปลง Response และแสดงภาพ ----------
    // แปลง response body ของภาพ PNG เป็น Blob ที่ Browser ใช้งานได้
    const resultBlob = await response.blob();
    // Object URL อ้างหน่วยความจำไว้ จึงยกเลิก URL รอบก่อนก่อนสร้างค่าใหม่
    if (originalUrl) URL.revokeObjectURL(originalUrl);
    if (processedUrl) URL.revokeObjectURL(processedUrl);

    // สร้าง URL ชั่วคราวสำหรับ preview ไฟล์ต้นฉบับจากเครื่องผู้ใช้
    originalUrl = URL.createObjectURL(file);
    // สร้าง URL ชั่วคราวสำหรับ Blob ผลลัพธ์จาก Server
    processedUrl = URL.createObjectURL(resultBlob);
    // กำหนด src ของภาพทั้งสองให้ Browser แสดง Object URL
    originalImage.src = originalUrl;
    processedImage.src = processedUrl;
    // ใช้ Blob เดียวกับภาพผลลัพธ์เป็นไฟล์ปลายทางของลิงก์ดาวน์โหลด
    downloadLink.href = processedUrl;
    // เปลี่ยน hidden property เพื่อแสดง section ผลลัพธ์
    results.hidden = false;
    // เปลี่ยนสีและข้อความสถานะเมื่อทุกขั้นตอนสำเร็จ
    statusText.className = "success";
    statusText.textContent = "ประมวลผลเสร็จแล้ว";
  // ---------- 3.4 จัดการข้อผิดพลาดและคืนสถานะปุ่ม ----------
  } catch (error) {
    // ครอบคลุม network error, JSON/Blob error และ Error ที่โยนจาก HTTP status
    statusText.className = "error";
    statusText.textContent =
      error instanceof TypeError
        ? "เชื่อมต่อ Backend ไม่ได้ กรุณาตรวจสอบ URL, เครือข่าย และ Firewall"
        : error.message;
  } finally {
    // finally ทำงานเสมอ จึงเปิดปุ่มได้ทั้งกรณีสำเร็จและผิดพลาด
    submitButton.disabled = false;
  }
});

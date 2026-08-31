// เลือก element จากหน้า HTML เพื่อใช้รับข้อมูลและแสดงผล
const form = document.querySelector("#upload-form");
const fileInput = document.querySelector("#image-file");
const statusText = document.querySelector("#status");
const submitButton = document.querySelector("#submit-button");
const results = document.querySelector("#results");
const originalImage = document.querySelector("#original-image");
const processedImage = document.querySelector("#processed-image");
const downloadLink = document.querySelector("#download-link");

let originalUrl;
let processedUrl;

// ทำงานเมื่อผู้ใช้กดปุ่ม "ประมวลผลภาพ"
form.addEventListener("submit", async (event) => {
  // ป้องกัน Browser โหลดหน้าเว็บใหม่หลัง submit form
  event.preventDefault();
  const file = fileInput.files[0];
  if (!file) return;

  submitButton.disabled = true;
  statusText.className = "loading";
  statusText.textContent = "กำลังส่งภาพไปประมวลผล...";

  try {
    // FormData จะรวมไฟล์ภาพและ operation แล้วส่งไปยัง FastAPI Frontend
    const formData = new FormData(form);
    const response = await fetch("/api/process", { method: "POST", body: formData });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "ประมวลผลภาพไม่สำเร็จ");
    }

    // รับภาพ PNG ที่ Server ส่งกลับมาในรูปแบบ Blob
    const resultBlob = await response.blob();
    // ยกเลิก URL เก่าก่อนสร้าง URL ใหม่ เพื่อไม่ให้ใช้หน่วยความจำค้างไว้
    if (originalUrl) URL.revokeObjectURL(originalUrl);
    if (processedUrl) URL.revokeObjectURL(processedUrl);

    originalUrl = URL.createObjectURL(file);
    processedUrl = URL.createObjectURL(resultBlob);
    // แสดงภาพต้นฉบับ ภาพผลลัพธ์ และกำหนดลิงก์ดาวน์โหลด
    originalImage.src = originalUrl;
    processedImage.src = processedUrl;
    downloadLink.href = processedUrl;
    results.hidden = false;
    statusText.className = "success";
    statusText.textContent = "ประมวลผลเสร็จแล้ว";
  } catch (error) {
    // แสดงข้อความเมื่อ Backend ไม่พร้อม หรือไฟล์ไม่ผ่านการตรวจสอบ
    statusText.className = "error";
    statusText.textContent = error.message;
  } finally {
    // เปิดปุ่มให้กดใหม่ได้ ไม่ว่าคำขอจะสำเร็จหรือเกิดข้อผิดพลาด
    submitButton.disabled = false;
  }
});

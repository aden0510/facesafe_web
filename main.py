from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
import cv2
import numpy as np
import os
import uuid

app = FastAPI(title="FaceSafe Web Demo", description="페이스안심 웹 시연")

UPLOAD_DIR = "temp_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def main_page():
    # 누구나 브라우저로 접속해 사진을 올릴 수 있는 초간단 시연용 웹 UI
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>페이스안심 (FaceSafe) 웹 데모</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #f4f6f9; }
            .container { background: white; padding: 30px; border-radius: 12px; display: inline-block; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
            input[type="file"] { margin: 20px 0; }
            button { background-color: #4f46e5; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-size: 16px; cursor: pointer; }
            button:hover { background-color: #4338ca; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🛡️ 페이스안심 (FaceSafe) 웹 시연</h2>
            <p>사진을 업로드하면 딥페이크 방어 고밀도 그레인 노이즈가 적용됩니다.</p>
            <form action="/protect" method="post" enctype="multipart/form-data">
                <input type="file" name="file" accept="image/*" required><br>
                <button type="submit">방어 적용 및 다운로드</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/protect")
async def protect_image(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"input_{file_id}.jpg")
    output_path = os.path.join(UPLOAD_DIR, f"protected_{file_id}.jpg")
    
    contents = await file.read()
    with open(input_path, "wb") as f:
        f.write(contents)
        
    img = cv2.imread(input_path)
    if img is not None:
        # 필름 그레인 스타일의 미세 고주파 노이즈 결합 시뮬레이션
        noise = np.random.normal(0, 8, img.shape).astype(np.int16)
        protected_img = cv2.add(img.astype(np.int16), noise).clip(0, 255).astype(np.uint8)
        cv2.imwrite(output_path, protected_img)
    else:
        output_path = input_path

    return FileResponse(output_path, media_type="image/jpeg", filename="facesafe_protected.jpg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
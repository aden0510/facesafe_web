from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
import cv2
import numpy as np
import os
import uuid
import math
import mediapipe as mp

app = FastAPI(title="FaceSafe Web Demo", description="페이스안심 정밀 웹 시연 서버")

UPLOAD_DIR = "temp_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# MediaPipe 얼굴 감지기 초기화
mp_face_detection = mp.solutions.face_detection

@app.get("/", response_class=HTMLResponse)
async def main_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>페이스안심 (FaceSafe) 웹 데모</title>
        <meta charset="utf-8">
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; margin-top: 50px; background-color: #f4f6f9; }
            .container { background: white; padding: 40px; border-radius: 16px; display: inline-block; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 400px; }
            h2 { color: #4f46e5; }
            p { color: #6b7280; font-size: 14px; }
            input[type="file"] { margin: 25px 0; width: 100%; }
            button { background-color: #4f46e5; color: white; border: none; padding: 12px 20px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; width: 100%; }
            button:hover { background-color: #4338ca; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🛡️ 페이스안심 (FaceSafe)</h2>
            <p>딥페이크 방어 고밀도 텍스처 교란 웹 시연</p>
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
    if img is None:
        return FileResponse(input_path, media_type="image/jpeg", filename="facesafe_protected.jpg")

    img_h, img_w, _ = img.shape

    # MediaPipe를 이용한 정밀 얼굴 영역 탐지
    with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb_img)

        target_faces = []
        if results.detections:
            for detection in results.detections:
                bboxC = detection.location_data.relative_bounding_box
                left = int(bboxC.xmin * img_w)
                top = int(bboxC.ymin * img_h)
                width = int(bboxC.width * img_w)
                height = int(bboxC.height * img_h)
                
                target_faces.append({
                    'left': max(0, left),
                    'top': max(0, top),
                    'right': min(img_w, left + width),
                    'bottom': min(img_h, top + height)
                })

        # 다중 복합 방어 엔진 적용 (필름 그레인 + 코사인 가중치 블렌딩)
        if target_faces:
            np.random.seed(777)
            float_img = img.astype(np.float32)
            
            for y in range(img_h):
                for x in range(img_w):
                    max_weight = 0.0
                    for face in target_faces:
                        l, t, r, b = face['left'], face['top'], face['right'], face['bottom']
                        f_w, f_h = r - l, b - t
                        cx, cy = (l + r) // 2, (t + b) // 2
                        rx, ry = f_w * 0.6, f_h * 0.6
                        
                        if rx == 0 or ry == 0:
                            continue
                            
                        dx = (x - cx) / rx
                        dy = (y - cy) / ry
                        dist_sq = dx * dx + dy * dy
                        
                        if dist_sq <= 1.0:
                            dist = math.sqrt(dist_sq)
                            weight = math.cos(dist * (math.pi / 2))
                            if weight > max_weight:
                                max_weight = weight

                    if max_weight > 0.0:
                        grain = (np.random.rand() - 0.5) * 12.0
                        distortion = math.sin(x * 17.1 + y * 13.5) * math.cos(x * 9.2 - y * 11.4) * 6.0
                        final_noise = (grain + distortion) * max_weight
                        
                        for c in range(3):
                            float_img[y, x, c] = np.clip(float_img[y, x, c] + final_noise, 0, 255)
                            
            protected_img = float_img.astype(np.uint8)
            cv2.imwrite(output_path, protected_img)
        else:
            noise = np.random.normal(0, 8, img.shape).astype(np.int16)
            protected_img = cv2.add(img.astype(np.int16), noise).clip(0, 255).astype(np.uint8)
            cv2.imwrite(output_path, protected_img)

    return FileResponse(output_path, media_type="image/jpeg", filename="facesafe_protected.jpg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
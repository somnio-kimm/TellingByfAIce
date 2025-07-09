from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import numpy as np
import base64
import cv2
import io
import traceback
from PIL import Image
from contextlib import asynccontextmanager

from app.prompt_chain import chain
from app.util import load_detector, load_classifier, crop_face, predict_expression

# ========== Camera Lifecycle ==========
camera = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global camera
    camera = cv2.VideoCapture(0)
    print("📸 Camera started")
    yield
    camera.release()
    print("🛑 Camera released")

# ========== FastAPI App ==========
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== Load Models ==========
detection_model = load_detector()
classification_model = load_classifier()

if detection_model is None or classification_model is None:
    raise RuntimeError("❌ Failed to load one or more models")

# ========== Pydantic Models ==========
class ExpressionPrompt(BaseModel):
    text: str
    expected_emotion: str

class EmotionImage(BaseModel):
    image: str  # ✅ Matches Godot `{ "image": base64_str }`

# ========== Routes ==========

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/generate_expression_prompt/", response_model=ExpressionPrompt)
async def generate_prompt():
    try:
        result = await chain.ainvoke({})
        print("📥 Chain output:", result)
        return result
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/capture_image/")
def capture_image():
    try:
        global camera
        if camera is None or not camera.isOpened():
            print("🔄 Reinitializing camera...")
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                return JSONResponse(content={"error": "Camera could not be opened"}, status_code=500)

        ret, frame = camera.read()
        if not ret or frame is None:
            return JSONResponse(content={"error": "Failed to read from camera"}, status_code=500)

        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized_frame = cv2.resize(rgb_image, (244, 244))
        pil_image = Image.fromarray(rgb_image)

        try:
            cropped, bbox = crop_face(model=detection_model, image=pil_image)
        except Exception as e:
            print("⚠️ Face detection failed:", e)
            cropped = pil_image
            bbox = None

        emotion_probs, emotion = predict_expression(model=classification_model, image=cropped)
        top_confidence = emotion_probs[emotion] if emotion in emotion_probs else 0.0

        bgr_resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_RGB2BGR)
        success, buffer = cv2.imencode('.jpg', bgr_resized_frame)
        if not success:
            return JSONResponse(content={"error": "Failed to encode image"}, status_code=500)

        img_bytes = base64.b64encode(buffer).decode("utf-8")

        response_data = {
            "image": img_bytes,
            "emotion": emotion,
            "top_confidence": top_confidence,
            "emotion_probs": {k: float(v) for k, v in emotion_probs.items()},
            "frame_shape": {
                "width": resized_frame.shape[1],
                "height": resized_frame.shape[0]
            },
            "bounding_box": {
                "x_min": bbox[0],
                "y_min": bbox[1],
                "x_max": bbox[2],
                "y_max": bbox[3]
            } if bbox else None,
            "original_frame_shape": {
                "width": frame.shape[1],
                "height": frame.shape[0]
            }
        }

        print(f"📦 BBox: {bbox} | 🧠 Emotion: {emotion} ({top_confidence:.2f}) | 🔢 Probs: {emotion_probs}")
        return JSONResponse(content=response_data)

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": "Failed in /capture_image: " + str(e)})

@app.post("/predict_emotion/")
async def predict_emotion(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        try:
            cropped, bbox = crop_face(model=detection_model, image=image)
        except Exception as e:
            print("⚠️ Face detection failed:", e)
            cropped = image
            bbox = None

        emotion_probs, emotion = predict_expression(model=classification_model, image=cropped)
        top_confidence = emotion_probs[emotion] if emotion in emotion_probs else 0.0

        response_data = {
            "emotion": emotion,
            "top_confidence": top_confidence,
            "emotion_probs": {k: float(v) for k, v in emotion_probs.items()},
            "bounding_box": {
                "x_min": bbox[0],
                "y_min": bbox[1],
                "x_max": bbox[2],
                "y_max": bbox[3]
            } if bbox else {
                "x_min": 0,
                "y_min": 0,
                "x_max": 0,
                "y_max": 0
            }
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        tb_io = io.StringIO()
        traceback.print_exc(file=tb_io)
        error_details = tb_io.getvalue()
        return JSONResponse(
            content={
                "error": f"Failed in /predict_emotion: {str(e)}",
                "traceback": error_details
            },
            status_code=500
        )
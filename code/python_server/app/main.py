# main.py
# Communicate with game engine

import numpy as np
import base64
import cv2
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from PIL import Image
import torch

from app.util import load_detector, load_classifier, crop_face, predict_expression, draw_emotion_box
from app.prompt_chain import generate_scenario

# Global webcam instance
camera = None

# App lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
	global camera
	camera = cv2.VideoCapture(0)
	print("📸 Camera started")
	yield
	camera.release()
	print("🔒 Camera released")

# FastAPI app setup
app = FastAPI(lifespan=lifespan)
detection_model = load_detector()
classification_model = load_classifier()

@app.get("/")
def root():
	return {"message": "Facial Expression API is running."}

@app.post("/predict/")
async def predict():
	ret, frame = camera.read()
	if not ret:
		return JSONResponse({"error": "Webcam capture failed"}, status_code=500)

	try:
		# Convert to PIL
		image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		pil_image = Image.fromarray(image)

		# Crop face, get bbox and original image
		image_cropped, bbox, image_orig = crop_face(detection_model, pil_image)
		frame_to_draw = cv2.cvtColor(np.array(image_orig), cv2.COLOR_RGB2BGR)

		if image_cropped and bbox:
			emotion, confidence, all_confidences = predict_expression(classification_model, image_cropped)
			frame_to_draw = draw_emotion_box(frame_to_draw, bbox, emotion, confidence)
		else:
			emotion, confidence = "no_face", 0.0
			all_confidences = None
			print("⚠️ No face detected")

		# Encode image with box
		frame_to_draw = cv2.resize(frame_to_draw, (300, 300))
		success, buffer = cv2.imencode('.jpg', frame_to_draw)
		if not success:
			return JSONResponse({"error": "Failed to encode image"}, status_code=500)

		img_bytes = base64.b64encode(buffer).decode("utf-8")
		return JSONResponse({
			"emotion": emotion,
			"confidence": confidence,
			"bbox": bbox,
			"image": img_bytes,
			"all_confidences": all_confidences
		})

	except Exception as e:
		import traceback
		print(traceback.format_exc())
		return JSONResponse({"error": str(e)}, status_code=500)
	
@app.get("/generate_scenario")
async def get_scenario():
    try:
        result = generate_scenario()
        return JSONResponse({"scenario": result["text"]})
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JSONResponse({"error": str(e)}, status_code=500)
	
@app.get("/start_recording")
async def start_recording_endpoint():
    try:
        start_recording()
        return {"status": "recording_started"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/transcribe")
async def stop_and_transcribe_endpoint():
    try:
        transcript = transcribe()
        return {"transcript": transcript}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/evaluate_response")
async def evaluate_endpoint(payload: dict):
    try:
        scenario = payload.get("scenario", "")
        user_response = payload.get("user_response", "")
        result = evaluate_response(scenario, user_response)
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
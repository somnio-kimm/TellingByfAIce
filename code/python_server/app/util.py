# util.py
# Utility functions

# Libraries
import torch
import cv2
from PIL import Image
from torchvision import transforms
from ultralytics import YOLO

from app.config import DEVICE, DETECTOR_PATH, CLASSIFIER_WEIGHT_PATH, EMOTION, EMOTION_MAP, IMAGE_SIZE
from model.model_arch import EmotionClassifier

# Load face detector
def load_detector():
	model = YOLO(DETECTOR_PATH, task="detect")
	return model

# Load emotion classifier
def load_classifier():
	model = EmotionClassifier()
	model.load_state_dict(torch.load(CLASSIFIER_WEIGHT_PATH, map_location=DEVICE))
	model.eval()
	return model

# def load_classifier():
#     model = EmotionClassifier()
#     try:
#         state_dict = torch.load(CLASSIFIER_WEIGHT_PATH, map_location=DEVICE)
#         model.load_state_dict(state_dict)
#     except Exception as e:
#         print("❌ Failed to load classifier weights:", e)
#         import traceback; traceback.print_exc()
#         return None
#     model.eval()
#     return model

# Detect face and return cropped face, bbox, and original image
def crop_face(model, image_orig: Image.Image):
	result = model(image_orig)[0]
	boxes = result.boxes

	if len(boxes) == 0:
		return None, None, image_orig  # No face detected

	box = boxes[0]
	x_min, y_min, x_max, y_max = map(int, box.xyxy[0].tolist())
	image_cropped = image_orig.crop((x_min, y_min, x_max, y_max))

	print(f"📦 BBox: {x_min}, {y_min}, {x_max}, {y_max}")
	return image_cropped, (x_min, y_min, x_max, y_max), image_orig

# Image preprocessing
transform = transforms.Compose([
	transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
	transforms.ToTensor(),
	transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# Predict emotion from cropped face
def predict_expression(model, image: Image.Image):
	image_tensor = transform(image).unsqueeze(0).to(DEVICE)

	with torch.inference_mode():
		outputs = model(image_tensor)
		confidences = torch.softmax(outputs, dim=1)[0]  # shape: [num_classes]

	idx = torch.argmax(confidences).item()
	emotion = EMOTION[idx]

	# Map all emotions with their confidence scores
	all_confidences = {EMOTION_MAP[EMOTION[i]]: round(confidences[i].item(), 2) for i in range(len(EMOTION))}

	return EMOTION_MAP[emotion], round(confidences[idx].item(), 2), all_confidences

# Draw bounding box and emotion label on OpenCV image
def draw_emotion_box(frame, bbox, emotion_label, confidences):
	if bbox is None:
		return frame

	x1, y1, x2, y2 = bbox
	color = (0, 255, 0)  # Green box
	thickness = 3
	font = cv2.FONT_HERSHEY_SIMPLEX
	font_scale = 0.9

	# Draw rectangle
	cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
	# Put emotion label
	cv2.putText(frame, f"{emotion_label} {confidences:.2f}", (x1, y1 - 10),
				font, font_scale, color, thickness, cv2.LINE_AA)

	return frame
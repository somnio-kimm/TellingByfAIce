# config.py
# Constants

# Library
import torch

# Constants
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
DETECTOR_PATH = "model/yolo.onnx"
CLASSIFIER_WEIGHT_PATH = "model/efficientnet_b3.pth" #"model/emotion_classifier.pth"
EMOTION = ["anger", "happy", "panic", "sadness"]
EMOTION_MAP = {"anger": "angry",
			   "happy": "happy",
			   "panic": "awe",
			   "sadness": "sad",
			   "blank": "blank"}
IMAGE_SIZE = 300 #224
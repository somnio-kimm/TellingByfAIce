# model_arch.py
# Store model architecture

# Library
import torch
from torch import nn
from torchvision import models
from torchvision.models import efficientnet_b3, EfficientNet_B3_Weights
import timm

#Emotion classifier
class EmotionClassifier(nn.Module):
	def __init__(self, num_classes=4):
		super().__init__()
		base_model = models.efficientnet_b3(pretrained=True)

		# 마지막 FC 레이어 제거
		self.features = base_model.features

		# Adaptive pooling 레이어 추가
		self.pooling = nn.AdaptiveAvgPool2d(1)  # (batch, 1536, 1, 1)

		# 새 출력 레이어 추가
		self.classifier = nn.Sequential(
			nn.Flatten(),
			nn.Linear(1536, 128),
			nn.ReLU(),
			nn.Linear(128, num_classes)
		)

	def forward(self, x):
		x = self.features(x)
		x = self.pooling(x)
		x = self.classifier(x)
		return x
	
# class EmotionClassifier(nn.Module):
# 	def __init__(self, num_classes=4):
# 		super().__init__()
# 		self.backbone = timm.create_model("vit_base_patch16_224", pretrained=True)
# 		self.num_features = self.backbone.head.in_features
# 		self.backbone.head = nn.Identity()
# 		self.fc_label = nn.Linear(self.num_features, num_classes)

# 	def forward(self, x):
# 		x = self.backbone(x)
# 		return self.fc_label(x)

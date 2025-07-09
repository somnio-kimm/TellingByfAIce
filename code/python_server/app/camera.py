import cv2
from PIL import Image
from app.util import (
    load_detector,
    load_classifier,
    crop_face,
    predict_expression,
    draw_emotion_box
)

# Load models
detector = load_detector()
classifier = load_classifier()

# Start webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Failed to open webcam")
    exit()

print("🎥 Webcam started. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to read frame.")
        break

    # Convert BGR (OpenCV) to RGB (PIL)
    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)

    try:
        # Detect face and crop
        image_cropped, bbox, _ = crop_face(detector, pil_image)

        if image_cropped is not None and bbox is not None:
            # Predict emotion
            emotion, confidence = predict_expression(classifier, image_cropped)
            # Draw bounding box and label on frame
            frame = draw_emotion_box(frame, bbox, emotion, confidence)
        else:
            print("⚠️ No face detected")
    except Exception as e:
        print(f"⚠️ Error during prediction: {e}")

    # Show annotated frame
    cv2.imshow("Emotion Detection", frame)

    # Break loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
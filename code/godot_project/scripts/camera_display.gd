extends Control

@onready var http_request = $http_request
@onready var camera_texture_rect = $camera_feed
@onready var confidence_label = $confidence_label  # adjust path as needed

signal emotion_predicted(predicted_emotion: String)

var is_snapshot_mode = false
var current_snapshot_image: Image
var countdown_seconds = 0  # seconds before taking snapshot

func _ready():
	if not http_request.request_completed.is_connected(_on_camera_response):
		http_request.request_completed.connect(_on_camera_response)
	fetch_camera_frame()

func fetch_camera_frame():
	var headers = ["Content-Type: application/json"]
	var body = PackedByteArray()  # Empty JSON `{}` payload
	body.append_array("{}".to_utf8_buffer())

	http_request.request_raw(
		"http://127.0.0.1:8000/predict/",
		headers,
		HTTPClient.METHOD_POST,
		body
	)
	
	#if err != OK:
		#print("❌ HTTP request error: ", err)

func _on_camera_response(result, response_code, headers, body):
	if response_code == 200:
		var json = JSON.parse_string(body.get_string_from_utf8())
		if json and json.has("image"):
			var image_data = Marshalls.base64_to_raw(json["image"])
			var image = Image.new()
			var err = image.load_jpg_from_buffer(image_data)
			if err == OK:
				# Update live camera texture with bounding box
				var texture = ImageTexture.create_from_image(image)
				camera_texture_rect.texture = texture

				# 🔎 Update confidence text
				if json.has("all_confidences") and typeof(json["all_confidences"]) == TYPE_DICTIONARY:
					var confs = json["all_confidences"]
					var conf_text = "Confidences:\n"
					for key in confs:
						conf_text += "%s: %.2f\n" % [key.capitalize(), confs[key]]
					confidence_label.text = conf_text
				else:
					print("⚠️ Confidences are missing or not a dictionary")

				# 🟡 Use emotion only when snapshot mode is active
				if is_snapshot_mode:
					is_snapshot_mode = false
					current_snapshot_image = image.duplicate()

					if json.has("emotion"):
						var predicted = json["emotion"]
						print("🎯 Emotion locked in: ", predicted)
						emit_signal("emotion_predicted", predicted)
			else:
				print("❌ Failed to load JPG buffer")
	else:
		print("❌ Server returned status: ", response_code)

	await get_tree().create_timer(0.1).timeout
	fetch_camera_frame()

func start_snapshot():
	print("⏳ Countdown started...")
	for i in range(countdown_seconds, 0, -1):
		print("⏱️ ", i)
		await get_tree().create_timer(1.0).timeout

	print("📸 Countdown finished — capturing next frame...")
	is_snapshot_mode = true

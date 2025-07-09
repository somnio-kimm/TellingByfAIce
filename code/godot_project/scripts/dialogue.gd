extends Control

@export var countdown_duration: int = 3

signal dialogue_finished
signal emotion_check_required(emotion_true: String)
signal lose_heart(amount: int)
signal typing_finished

@onready var dialogue_label: RichTextLabel = $dialogue_panel/dialogue_label
@onready var timer_label: Label = $timer_panel/timer_label
@onready var auto_advance_timer: Timer = $auto_advance_timer
@onready var background_image: TextureRect = $background_image
@onready var character_image: TextureRect = $character_image

var dialogue_lines: Array = []
var current_index := 0
var is_waiting_for_emotion := false
var emotion_true := ""
var is_typing := false
var typing_speed := 0.05

var fail_text := ""
var timer := false
var countdown := 3
var is_handling_fail := false
var fail_text_done := false
var previous_background_path := ""
var has_ended := false

func _ready():
	dialogue_label.bbcode_enabled = true
	auto_advance_timer.timeout.connect(_on_auto_advance_timeout) 

func start_dialogue(lines: Array):
	dialogue_lines = lines
	current_index = 0
	is_waiting_for_emotion = false
	is_handling_fail = false
	has_ended = false
	show_dialogue()

func show_dialogue() -> void:
	if has_ended:
		return 

	is_typing = false

	if current_index >= dialogue_lines.size():
		has_ended = true
		emit_signal("dialogue_finished")
		return

	var entry: Dictionary = dialogue_lines[current_index]
	var full_text: String = entry.get("text", " ")

	var is_end: bool = entry.get("end", false)
	var is_last_line: bool = current_index == dialogue_lines.size() - 1

	if is_end and is_last_line:
		has_ended = true
		type_text(full_text, func(): emit_signal("dialogue_finished"))
		return

	# Background
	var bg_path = entry.get("background", "")
	if bg_path != "" and ResourceLoader.exists(bg_path):
		background_image.texture = load(bg_path)
		previous_background_path = bg_path
	else:
		print("❌ Missing background file:", bg_path)

	# Character
	var char_path = entry.get("character", "")
	if char_path != "" and ResourceLoader.exists(char_path):
		character_image.texture = load(char_path)
	else:
		character_image.texture = null

	is_waiting_for_emotion = entry.has("emotion_expected")
	emotion_true = entry.get("emotion_expected", "")
	fail_text = entry.get("failure_text", "")
	timer = entry.get("timer", false)
	auto_advance_timer.stop()

	if timer:
		countdown = countdown_duration
		timer_label.visible = true
		timer_label.text = str(countdown)
		auto_advance_timer.start()

	if is_waiting_for_emotion:
		emit_signal("emotion_check_required", emotion_true)

	print("🧠 Line:", current_index, "/", dialogue_lines.size())
	print("📝 Entry:", entry)

	type_text(full_text)

func advance_dialogue():
	if is_waiting_for_emotion:
		print("⛔ Emotion check in progress")
		return

	if is_handling_fail:
		if fail_text_done:
			_on_fail_text_finished()
		else:
			print("⛔ Fail text still typing")
		return

	if timer and auto_advance_timer.time_left > 0:
		print("⏳ Countdown active. Space ignored.")
		return

	timer_label.visible = false

	if is_typing:
		is_typing = false
		dialogue_label.bbcode_text = dialogue_lines[current_index].get("text", " ")
	else:
		current_index += 1
		show_dialogue()

func type_text(full_text: String, callback_on_finish: Callable = Callable(), is_fail_text: bool = false) -> void:
	is_typing = true
	if is_fail_text:
		fail_text_done = false

	var visible_text := ""
	for i in full_text.length():
		if not is_typing:
			break
		visible_text += full_text[i]
		dialogue_label.bbcode_text = visible_text
		await get_tree().create_timer(typing_speed).timeout

	is_typing = false
	dialogue_label.bbcode_text = full_text
	emit_signal("typing_finished")

	if is_fail_text:
		fail_text_done = true

	if callback_on_finish.is_valid():
		callback_on_finish.call()

func _on_auto_advance_timeout():
	if is_typing or is_waiting_for_emotion or is_handling_fail:
		auto_advance_timer.start()
		return

	countdown -= 1
	if countdown <= 0:
		advance_dialogue()
	else:
		timer_label.text = str(countdown)
		auto_advance_timer.start()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_SPACE:
			advance_dialogue()

func _on_fail_text_finished():
	is_handling_fail = false
	fail_text_done = false

	if heart.get_remaining_hearts() <= 0:
		print("🛑 Failure text complete — hearts depleted")
		emit_signal("dialogue_finished")
	else:
		current_index += 1
		show_dialogue()

func on_emotion_result(emotion_pred: String) -> void:
	print("📩 Emotion detected:", emotion_pred)
	auto_advance_timer.stop()

	if not is_waiting_for_emotion:
		print("⛔ Not waiting for emotion")
		return

	is_waiting_for_emotion = false

	var normalized_pred = emotion_pred.strip_edges().to_lower()
	var normalized_true = emotion_true.strip_edges().to_lower()

	var entry = dialogue_lines[current_index]

	if normalized_pred == normalized_true:
		print("✅ Emotion matched")
		current_index += 1
		show_dialogue()
	else:
		print("❌ Emotion mismatched")
		emit_signal("lose_heart")
		is_handling_fail = true
		fail_text_done = false

		# Show fail visuals
		if entry.has("failure_character"):
			var fail_char_path = entry["failure_character"]
			if ResourceLoader.exists(fail_char_path):
				character_image.texture = load(fail_char_path)

		if entry.has("failure_background"):
			var fail_bg_path = entry["failure_background"]
			if ResourceLoader.exists(fail_bg_path):
				background_image.texture = load(fail_bg_path)

		# Show fail text and allow space to advance after it's fully typed
		type_text(fail_text, Callable(), true)

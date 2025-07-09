extends Control

@export var stage_index: int = 0
#@export var heart_loss: int = 0

#var stage_index: int = 0
var heart_loss: int = 0

@onready var bgm_player = $bgm_player
@onready var dialogue = $dialogue

enum StagePhase {INTRO, MAIN, GAME_OVER}
var phase = StagePhase.INTRO
var waiting_for_game_over = false

func _ready():
	if camera_display:
		camera_display.visible = true
	if heart:
		heart.visible = true
		if not heart.hearts_depleted.is_connected(_on_hearts_depleted):
			heart.hearts_depleted.connect(_on_hearts_depleted)
	
	bgm_player.play()

	dialogue.typing_finished.connect(_on_typing_finished)
	dialogue.emotion_check_required.connect(_on_emotion_check_required)
	dialogue.lose_heart.connect(_on_lose_heart)
	dialogue.dialogue_finished.connect(_on_dialogue_finished)
	camera_display.emotion_predicted.connect(_on_emotion_predicted)

	load_stage_dialogue("intro")

func load_stage_dialogue(stage_type: String):
	var path = "res://dialogues/stage_%d_%s.json" % [stage_index, stage_type]
	print("Loading dialogue: ", path)

	if FileAccess.file_exists(path):
		var file = FileAccess.open(path, FileAccess.READ)
		var parsed = JSON.parse_string(file.get_as_text())

		if typeof(parsed) == TYPE_DICTIONARY and parsed.has("dialogue"):
			if parsed.has("bgm"):
				bgm_player.stream = load(parsed["bgm"])
				bgm_player.stream.loop = true
				bgm_player.play()
			dialogue.start_dialogue(parsed["dialogue"])  # ✅ Always start dialogue
		else:
			push_error("Invalid dialogue file format: %s" % path)
	else:
		push_error("Dialogue file not found: %s" % path)

func _on_typing_finished():
	if dialogue.is_waiting_for_emotion:
		camera_display.start_snapshot()

func _on_emotion_check_required(expected_emotion: String):
	print("🎯 Expecting emotion:", expected_emotion)

func _on_emotion_predicted(predicted_emotion: String):
	print("📨 Received predicted:", predicted_emotion)
	dialogue.on_emotion_result(predicted_emotion)

func _on_lose_heart():
	print("💔 Lose ", heart_loss, " heart")
	heart.lose_heart(heart_loss)

func _on_dialogue_finished():
	print("Dialogue finished in phase:", phase)
	if waiting_for_game_over:
		print("▶️ Now loading game over dialogue")
		waiting_for_game_over = false
		await get_tree().create_timer(0.5).timeout
		load_stage_dialogue("game_over")
		return
	
	print("🧪 stage_index =", stage_index, ", heart_loss =", heart_loss)
	match phase:
		StagePhase.INTRO:
			phase = StagePhase.MAIN
			if stage_index == 5:
				get_tree().change_scene_to_file("res://scenes/shared/credits.tscn")
			else: 
				load_stage_dialogue("main")

		StagePhase.MAIN:
			phase = StagePhase.INTRO
			stage_index += 1
			update_heart_loss()
			update_countdown_duration()
			if stage_index <= 5:
				load_stage_dialogue("intro")

		StagePhase.GAME_OVER:
			print("💀 Game Over phase finished — preparing transition")
			await _prepare_game_over_transition()

func _on_hearts_depleted():
	print("💔 All hearts lost — waiting for failure dialogue to finish")
	phase = StagePhase.GAME_OVER
	waiting_for_game_over = true

func _prepare_game_over_transition():
	await get_tree().create_timer(1.0).timeout

	if camera_display:
		camera_display.visible = false

	if is_instance_valid(dialogue):
		print("✅ Dialogue valid")

		var bg_path = "res://assets/images/shared/game_over.png"
		if ResourceLoader.exists(bg_path):
			var texture = load(bg_path)
			dialogue.character_image.texture = null
			dialogue.background_image.texture = texture
			print("✅ Game Over background loaded")
		else:
			print("❌ Background path missing:", bg_path)

		if dialogue.has_node("dialogue_panel"):
			dialogue.get_node("dialogue_panel").visible = false
		if dialogue.has_node("timer_panel"):
			dialogue.get_node("timer_panel").visible = false

		await get_tree().create_timer(3.0).timeout
		dialogue.queue_free()

	bgm_player.stop()

	await get_tree().create_timer(0.1).timeout
	print("🧼 Scene cleanup done, now switching...")
	get_tree().change_scene_to_file("res://scenes/shared/title.tscn")

func update_heart_loss():
	match stage_index:
		0: heart_loss = 0
		1, 2: heart_loss = 1
		3: heart_loss = 2
		4: heart_loss = 4
		_: heart_loss = 1

func update_countdown_duration():
	match stage_index:  
		0, 1, 2: dialogue.countdown_duration = 3
		3: dialogue.countdown_duration = 2
		4: dialogue.countdown_duration = 1
		_: dialogue.countdown_duration = 3

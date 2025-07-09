extends Control
@onready var bgm_player = $bgm_player

func _ready():
	bgm_player.play()
	$button/story_mode.pressed.connect(_on_story_mode_pressed)
	$button/interactive_mode.pressed.connect(_on_interactive_mode_pressed)
	$button/credits.pressed.connect(_on_credits_pressed)
	$button/exit.pressed.connect(_on_exit_pressed)

func _on_story_mode_pressed():
	print("Game start")
	get_tree().change_scene_to_file("res://scenes/story_mode/stage.tscn")

func _on_interactive_mode_pressed():
	print("Game start")
	get_tree().change_scene_to_file("res://scenes/interactive_mode/stage.tscn")
	
func _on_credits_pressed():
	print("Credit")
	get_tree().change_scene_to_file("res://scenes/shared/credits.tscn")

func _on_exit_pressed():
	print("Exit")
	get_tree().quit()

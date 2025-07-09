extends Control

@onready var bgm_player = $bgm_player

func _ready():
	bgm_player.play()
	
	if camera_display:
		camera_display.visible = false
	if heart:
		heart.visible = false

func _input(event):
	if event is InputEventMouseButton and event.pressed:
		get_tree().change_scene_to_file("res://scenes/shared/title.tscn")

extends Control

signal hearts_depleted

@onready var hearts_container := $hearts_container

var hearts: Array
var hearts_curr: int = -1

func _ready():
	hearts = hearts_container.get_children()
	if hearts_curr == -1:
		hearts_curr = hearts.size()
	update_heart(hearts_curr)

func lose_heart(heart_loss: int = 0):
	hearts_curr -= heart_loss
	print("💔 Hearts remaining: ", hearts_curr)
	update_heart(hearts_curr)
	if hearts_curr <= 0:
		emit_signal("hearts_depleted")

func update_heart(value: int):
	for i in range(hearts.size()):
		hearts[i].visible = i < value
		
func get_remaining_hearts() -> int:
	return hearts_curr

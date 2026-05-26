# Cabinet Texture Workbench

Use this folder to choose the closest vanilla cabinet texture set for each Wildcraft wood.

Folders:
- `basegame/1block/`: exact copy of the base game one-block cabinet textures.
- `wildcraft_planks/`: current Wildcraft plank textures grouped by wood.
- `current_rotated_placeholders/`: the temporary rotated plank textures currently used by the mod.
- `sheets/`: visual contact sheets for quicker comparison.

Decision file:
- Fill `choices.csv`.
- `wildcraft_wood` is the target Wildcraft wood.
- `basegame_wood` should be one value from `available_basegame_woods.txt`.
- `tint_offset_hex` is optional. Leave blank unless you want a color nudge after matching average plank color. Use values like `#100800` or `#-080400` if needed; we can refine the format when applying it.

When you are done choosing, tell me to process `cabinet_texture_workbench/choices.csv`. I will generate tinted cabinet textures and wire the mod back to those generated cabinet texture paths.

#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path
from shutil import copy2
from typing import Iterable

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'cabinet_texture_workbench'
CHOICES = WORK / 'choices.csv'
VANILLA = Path('/home/matthewg/.local/share/vintagestory/assets/survival/textures/block/wood/cabinet/1block')
PLANKS = ROOT / 'assets/wildcrafttree/textures/block/wood/planks'
OUT = ROOT / 'assets/wildcrafttree/textures/block/wood/cabinet/1block'
PREVIEW = WORK / 'generated_preview'

CHOICE_ALIASES = {
    'larrch': 'larch',
    'very aged': 'veryaged',
    'very_aged': 'veryaged',
    'very-aged': 'veryaged',
    'ebody': 'ebony',
}

# The vanilla asset has this typo for one file. Treat it as walnut when using it as a source.
SOURCE_ALIASES = {
    'walnut': {'wallnut'},
}

VALID_BASE = {
    'acacia', 'aged', 'baldcypress', 'birch', 'ebony', 'kapok', 'larch',
    'maple', 'oak', 'pine', 'purpleheart', 'redwood', 'veryaged', 'walnut',
}

ALPHA_MIN = 8

def normalize_choice(value: str) -> str:
    value = value.strip().lower().replace(' ', '') if value.strip().lower() not in CHOICE_ALIASES else value.strip().lower()
    return CHOICE_ALIASES.get(value, value)

def image_mean(paths: Iterable[Path]) -> tuple[float, float, float]:
    total = [0.0, 0.0, 0.0]
    count = 0
    for path in paths:
        with Image.open(path) as im:
            for r, g, b, a in im.convert('RGBA').getdata():
                if a >= ALPHA_MIN:
                    total[0] += r
                    total[1] += g
                    total[2] += b
                    count += 1
    if count == 0:
        return (128.0, 128.0, 128.0)
    return (total[0] / count, total[1] / count, total[2] / count)

def parse_offset(value: str) -> tuple[int, int, int]:
    value = value.strip()
    if not value:
        return (0, 0, 0)
    if value.startswith('#'):
        value = value[1:]
    if len(value) == 6 and all(c in '0123456789abcdefABCDEF' for c in value):
        return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))
    if value.startswith(('+', '-')) and len(value) == 7:
        sign = -1 if value[0] == '-' else 1
        raw = value[1:]
        if all(c in '0123456789abcdefABCDEF' for c in raw):
            return tuple(sign * int(raw[i:i+2], 16) for i in (0, 2, 4))
    raise ValueError(f'Unsupported tint_offset_hex value: {value!r}')

def clamp(v: float) -> int:
    return max(0, min(255, int(round(v))))

def source_paths_for(basewood: str) -> list[Path]:
    names = {basewood} | SOURCE_ALIASES.get(basewood, set())
    paths = []
    for path in VANILLA.rglob('*.png'):
        if path.stem in names:
            paths.append(path)
    if not paths:
        raise FileNotFoundError(f'No vanilla cabinet textures found for {basewood}')
    return sorted(paths)

def target_planks_for(wood: str) -> list[Path]:
    paths = [PLANKS / f'{wood}{i}.png' for i in range(1, 5)]
    missing = [p for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(f'Missing plank textures for {wood}: {missing}')
    return paths

def tint_image(src: Path, dst: Path, scale: tuple[float, float, float], offset: tuple[int, int, int]) -> None:
    with Image.open(src) as im:
        rgba = im.convert('RGBA')
        out = []
        for r, g, b, a in rgba.getdata():
            if a < ALPHA_MIN:
                out.append((r, g, b, a))
            else:
                out.append((
                    clamp(r * scale[0] + offset[0]),
                    clamp(g * scale[1] + offset[1]),
                    clamp(b * scale[2] + offset[2]),
                    a,
                ))
        rgba.putdata(out)
        dst.parent.mkdir(parents=True, exist_ok=True)
        rgba.save(dst)

def main() -> None:
    with CHOICES.open(newline='') as f:
        rows = list(csv.DictReader(f))

    normalized_rows = []
    warnings = []
    generated = 0

    for row in rows:
        wood = row['wildcraft_wood'].strip()
        base_raw = row['basegame_wood'].strip()
        base = normalize_choice(base_raw)
        if not wood or not base:
            warnings.append(f'Skipping incomplete row: {row}')
            continue
        if base not in VALID_BASE:
            raise ValueError(f'Invalid basegame wood for {wood}: {base_raw!r} normalized to {base!r}')

        source_paths = source_paths_for(base)
        target_mean = image_mean(target_planks_for(wood))
        source_mean = image_mean(source_paths)
        offset = parse_offset(row.get('tint_offset_hex', ''))
        scale = tuple(target_mean[i] / source_mean[i] if source_mean[i] else 1.0 for i in range(3))

        for src in source_paths:
            rel = src.relative_to(VANILLA)
            # Normalize vanilla's wallnut typo into the target Wildcraft wood filename.
            dst = OUT / rel.with_name(f'{wood}.png')
            tint_image(src, dst, scale, offset)
            preview_dst = PREVIEW / rel.with_name(f'{wood}.png')
            tint_image(src, preview_dst, scale, offset)
            generated += 1

        normalized_rows.append({
            'wildcraft_wood': wood,
            'basegame_wood': base,
            'tint_offset_hex': row.get('tint_offset_hex', '').strip(),
            'notes': row.get('notes', '').strip(),
        })

    normalized = WORK / 'choices.normalized.csv'
    with normalized.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['wildcraft_wood', 'basegame_wood', 'tint_offset_hex', 'notes'])
        writer.writeheader()
        writer.writerows(normalized_rows)

    print(f'generated textures: {generated}')
    print(f'normalized choices: {normalized}')
    for warning in warnings:
        print(f'warning: {warning}')

if __name__ == '__main__':
    main()

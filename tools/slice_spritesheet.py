from pathlib import Path
from PIL import Image
from typing import Union, Tuple


def slice_spritesheet(
        source_path: Union[str, Path],
        tile_w: int,
        tile_h: int,
        name: str,
        save_dir: Union[str, Path],
        start: Tuple[int, int],  # (x, y) - координаты начала (1-based)
        end: Tuple[int, int]  # (x, y) - координаты конца (1-based)
) -> int:
    """
    Нарезает спрайтшит по заданному диапазону тайлов.

    :param source_path: Путь к исходному PNG
    :param tile_w: Ширина тайла
    :param tile_h: Высота тайла
    :param name: Базовое имя файла
    :param save_dir: Папка для сохранения
    :param start: (x, y) - начало выреза (1, 1 - верхний левый)
    :param end: (x, y) - конец выреза
    :return: Количество сохранённых тайлов
    """

    src = Path(source_path)
    out = Path(save_dir)
    out.mkdir(parents=True, exist_ok=True)

    img = Image.open(src).convert("RGBA")
    img_w, img_h = img.size

    # Максимально возможные координаты (1-based)
    max_x = img_w // tile_w
    max_y = img_h // tile_h

    sx, sy = start
    ex, ey = end

    # Проверка границ
    if sx < 1 or sy < 1:
        raise ValueError("Координаты start должны быть >= 1")
    if ex < sx or ey < sy:
        raise ValueError("Координаты end должны быть >= start")
    if ex > max_x or ey > max_y:
        raise ValueError(f"Координаты end {end} выходят за границы тайлов ({max_x}x{max_y})")

    count = 0

    # Проходим по строкам (Y) сверху вниз, затем по колонкам (X) слева направо
    for y in range(sy, ey + 1):
        for x in range(sx, ex + 1):
            left = (x - 1) * tile_w
            top = (y - 1) * tile_h

            box = (left, top, left + tile_w, top + tile_h)
            tile = img.crop(box)

            # Сохраняем: name_0.png, name_1.png...
            filename = f"{name}_{count}.png"
            tile.save(out / filename, "PNG")
            count += 1

    print(f"✅ {name}: вырезано {count} тайлов из {start} в {end}.")
    return count


slice_spritesheet(
    source_path=r"..\resources\GandalfHardcore FREE Warrior\GandalfHardcore Warrior.png",
    tile_w=80,
    tile_h=64,
    name="fail",
    save_dir="../assets/warrior",
    start=(1, 6),
    end=(4, 6)
)

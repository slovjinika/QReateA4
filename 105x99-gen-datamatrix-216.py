#!/usr/bin/env python3
import os
import math
from pystrich.datamatrix import DataMatrixEncoder
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# 1. MAIN SETTINGS AND PATHS
# ==========================================
FONT_PATH = "/home/node17/.fonts/002-Inter/Inter/static/Inter-Bold.otf"
OUTPUT_PDF = "print/labels_a4.pdf"
DPI = 600

# Range of numbers for generation
START_NUM = 1955
END_NUM = 2170

# ==========================================
# 2. COLOR AND FONT CONFIGURATION
# ==========================================
COLOR_BACKGROUND = "white"
COLOR_ELEMENTS = "#4D4D4D"

# OpenType features set for Inter font
FONT_FEATURES = ["tnum", "cv01", "cv05", "cv06", "calt"]

# ==========================================
# 3. STRICT STICKER GEOMETRY (IN MILLIMETERS)
# ==========================================
PAGE_W_MM = 210
PAGE_H_MM = 297
BLOCK_W_MM = 105
BLOCK_H_MM = 99

STICKER_W_MM = 13.5
STICKER_H_MM = 15.7
BORDER_MM = 0.35

GAP_X_MM = -0.5
GAP_Y_MM = -0.5

TEXT_ZONE_RATIO = 0.22
FONT_SIZE_PT = 6
TEXT_Y_SHIFT_MM = -1

QR_PADDING_MM = -0.5
QR_SCALE_FACTOR = 1.1

ROW_1_SHIFT_MM = 0.0
ROW_2_SHIFT_MM = 0.0
ROW_3_SHIFT_MM = 8

# ==========================================
# AUTOMATIC CONVERSION TO PIXELS
# ==========================================
MM_TO_PX = DPI / 25.4
PT_TO_PX = DPI / 72.0

A4_WIDTH = int(PAGE_W_MM * MM_TO_PX)
A4_HEIGHT = int(PAGE_H_MM * MM_TO_PX)
BLOCK_W = int(BLOCK_W_MM * MM_TO_PX)
BLOCK_H = int(BLOCK_H_MM * MM_TO_PX)

STICKER_W = int(STICKER_W_MM * MM_TO_PX)
STICKER_H = int(STICKER_H_MM * MM_TO_PX)
BORDER_PX = int(BORDER_MM * MM_TO_PX)

FONT_SIZE_PX = int(FONT_SIZE_PT * PT_TO_PX)
Y_SHIFT_PX = int(TEXT_Y_SHIFT_MM * MM_TO_PX)
QR_PADDING_PX = int(QR_PADDING_MM * MM_TO_PX)

TEXT_ZONE_H = int(STICKER_H * TEXT_ZONE_RATIO)
QR_ZONE_H = STICKER_H - TEXT_ZONE_H

QR_SIZE = min(STICKER_W - (BORDER_PX * 2) - (QR_PADDING_PX * 2), 
              QR_ZONE_H - BORDER_PX - QR_PADDING_PX)
QR_SIZE = int(QR_SIZE * QR_SCALE_FACTOR)

ROTATED_STICKER_W = STICKER_H
ROTATED_STICKER_H = STICKER_W
ROTATED_STICKER_W_MM = STICKER_H_MM
ROTATED_STICKER_H_MM = STICKER_W_MM

# ==========================================
# GENERATION FUNCTIONS
# ==========================================
def create_sticker(text, font_path):
    """Creates a single sticker with crisp DataMatrix and rotates it 90 degrees"""
    pystrich_bg = "ffffff" if COLOR_BACKGROUND == "white" else COLOR_BACKGROUND.lstrip('#')
    pystrich_el = COLOR_ELEMENTS.lstrip('#')

    # Генерация DataMatrix через pyStrich с базовым размером ячейки 1
    encoder = DataMatrixEncoder(text)
    dm_img = encoder.get_pilimage(cellsize=1, light_hex=pystrich_bg, dark_hex=pystrich_el)

    # Получаем исходные размеры матрицы
    orig_w, orig_h = dm_img.size

    # Вычисляем точный размер, кратный количеству модулей матрицы.
    # Это предотвращает появление полутоновых пикселей и «плывущих» границ.
    modules_count = orig_w
    module_px = max(1, round(QR_SIZE / modules_count))
    target_qr_size = modules_count * module_px

    # КРИТИЧЕСКИ ВАЖНО: NEAREST сохраняет идеальные черно-белые грани без сглаживания
    dm_img = dm_img.resize((target_qr_size, target_qr_size), Image.Resampling.NEAREST)

    # Создание стикера
    sticker = Image.new("RGB", (STICKER_W, STICKER_H), COLOR_BACKGROUND)
    draw = ImageDraw.Draw(sticker)

    qr_x = (STICKER_W - target_qr_size) // 2
    qr_y = BORDER_PX + QR_PADDING_PX
    sticker.paste(dm_img, (qr_x, qr_y))

    try:
        font = ImageFont.truetype(font_path, FONT_SIZE_PX)
    except IOError:
        font = ImageFont.load_default()

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    text_x = (STICKER_W - text_w) // 2
    text_y = QR_ZONE_H + ((TEXT_ZONE_H - text_h) // 2) + Y_SHIFT_PX

    try:
        draw.text((text_x, text_y), text, fill=COLOR_ELEMENTS, font=font, features=FONT_FEATURES)
    except ValueError:
        draw.text((text_x, text_y), text, fill=COLOR_ELEMENTS, font=font)

    draw.rectangle(
        [(0, 0), (STICKER_W - 1, STICKER_H - 1)], 
        outline=COLOR_ELEMENTS, 
        width=BORDER_PX
    )

    return sticker.rotate(90, expand=True)

# ==========================================
# A4 SHEET ASSEMBLY (6x6 GRID IN BLOCK)
# ==========================================
os.makedirs("print", exist_ok=True)
data_list = [f"{i:08d}" for i in range(START_NUM, END_NUM + 1)]

BLOCKS_X = 2
BLOCKS_Y = 3
COLS_PER_BLOCK = 6
ROWS_PER_BLOCK = 6
STICKERS_PER_BLOCK = COLS_PER_BLOCK * ROWS_PER_BLOCK  
STICKERS_PER_PAGE = BLOCKS_X * BLOCKS_Y * STICKERS_PER_BLOCK  

TOTAL_PAGES = math.ceil(len(data_list) / STICKERS_PER_PAGE)
pages = [Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white") for _ in range(TOTAL_PAGES)]

for idx, text in enumerate(data_list):
    page_idx = idx // STICKERS_PER_PAGE
    inside_page_idx = idx % STICKERS_PER_PAGE

    inside_page_block_idx = inside_page_idx // STICKERS_PER_BLOCK
    inside_block_idx = inside_page_idx % STICKERS_PER_BLOCK

    bx = inside_page_block_idx % BLOCKS_X  
    by = inside_page_block_idx // BLOCKS_X 

    block_left = bx * BLOCK_W
    block_top = by * BLOCK_H

    row_u = inside_block_idx // COLS_PER_BLOCK  
    col_u = inside_block_idx % COLS_PER_BLOCK   

    sx = row_u        
    sy = (COLS_PER_BLOCK - 1) - col_u    

    group_w_mm = (ROTATED_STICKER_W_MM * COLS_PER_BLOCK) + (GAP_X_MM * (COLS_PER_BLOCK - 1))
    group_h_mm = (ROTATED_STICKER_H_MM * ROWS_PER_BLOCK) + (GAP_Y_MM * (ROWS_PER_BLOCK - 1))

    margin_x_mm = (BLOCK_W_MM - group_w_mm) / 2
    margin_y_mm = (BLOCK_H_MM - group_h_mm) / 2  

    sticker_x = int(block_left + (margin_x_mm * MM_TO_PX) + (sx * (ROTATED_STICKER_W + GAP_X_MM * MM_TO_PX)))
    sticker_y = int(block_top + (margin_y_mm * MM_TO_PX) + (sy * (ROTATED_STICKER_H + GAP_Y_MM * MM_TO_PX)))

    if by == 0:
        sticker_y -= int(ROW_1_SHIFT_MM * MM_TO_PX)
    elif by == 1:
        sticker_y -= int(ROW_2_SHIFT_MM * MM_TO_PX)
    elif by == 2:
        sticker_y -= int(ROW_3_SHIFT_MM * MM_TO_PX)

    sticker_img = create_sticker(text, FONT_PATH)
    pages[page_idx].paste(sticker_img, (sticker_x, sticker_y))

# ==========================================
# DEBUG GRID ADDITION AND PDF SAVING
# ==========================================
DEBUG_GRID = True

if DEBUG_GRID:
    for page in pages:
        overlay = Image.new("RGBA", page.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        line_color = (255, 0, 255, 100)  

        x_105mm = int(105 * MM_TO_PX)
        x_210mm = int(210 * MM_TO_PX) - 1

        draw.line([(x_105mm, 0), (x_105mm, A4_HEIGHT)], fill=line_color, width=3)
        draw.line([(x_210mm, 0), (x_210mm, A4_HEIGHT)], fill=line_color, width=3)

        y_block1 = int(99 * MM_TO_PX)
        y_block2 = int(198 * MM_TO_PX)

        draw.line([(0, y_block1), (A4_WIDTH, y_block1)], fill=line_color, width=2)
        draw.line([(0, y_block2), (A4_WIDTH, y_block2)], fill=line_color, width=2)

        page.paste(Image.alpha_composite(page.convert("RGBA"), overlay).convert("RGB"))

if pages:
    pages[0].save(
        OUTPUT_PDF, 
        format="PDF",
        save_all=True, 
        append_images=pages[1:], 
        resolution=DPI,
        save_format="pdf",
        encoder_name="raw"
    )
    print(f"Done! PDF generated with crisp DataMatrix codes.")
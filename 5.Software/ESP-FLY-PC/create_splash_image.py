"""
创建启动画面图片
用于 PyInstaller 的 --splash 功能
"""

from PIL import Image, ImageDraw, ImageFont

# 创建图片（增加高度，留出更多空间给动态文本）
width, height = 500, 320
img = Image.new('RGB', (width, height), color='white')
draw = ImageDraw.Draw(img)

# 绘制边框
border_color = (41, 128, 185)  # 蓝色
draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=3)

# 绘制标题
try:
    # 尝试使用系统字体
    title_font = ImageFont.truetype("arial.ttf", 36)
    subtitle_font = ImageFont.truetype("arial.ttf", 16)
except:
    # 如果找不到，使用默认字体
    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()

# 标题文本（使用英文避免乱码）
title_text = "ESP-FLY-PC"
subtitle_text = "v2.0"
loading_text = "Loading..."

# 计算文本位置（居中）
title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
title_width = title_bbox[2] - title_bbox[0]
title_x = (width - title_width) // 2
title_y = height // 2 - 60

subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
subtitle_x = (width - subtitle_width) // 2
subtitle_y = title_y + 50

loading_bbox = draw.textbbox((0, 0), loading_text, font=subtitle_font)
loading_width = loading_bbox[2] - loading_bbox[0]
loading_x = (width - loading_width) // 2
loading_y = height - 80  # 上移，为动态文本留出空间

# 绘制文本
draw.text((title_x, title_y), title_text, fill=border_color, font=title_font)
draw.text((subtitle_x, subtitle_y), subtitle_text, fill='gray', font=subtitle_font)
draw.text((loading_x, loading_y), loading_text, fill='gray', font=subtitle_font)

# 绘制加载条背景
bar_x = 100
bar_y = height - 60
bar_width = width - 200
bar_height = 8
draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], 
               fill='lightgray', outline='gray')

# 在底部添加提示文本区域（为动态文本预留空间）
hint_font = subtitle_font
hint_text = "Initializing components..."
hint_bbox = draw.textbbox((0, 0), hint_text, font=hint_font)
hint_width = hint_bbox[2] - hint_bbox[0]
hint_x = (width - hint_width) // 2
hint_y = height - 30
# 绘制浅色提示文本（会被动态文本覆盖）
draw.text((hint_x, hint_y), hint_text, fill='lightgray', font=hint_font)

# 保存图片
img.save('splash.png')
print("启动画面已创建: splash.png")

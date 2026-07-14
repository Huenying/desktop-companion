#!/usr/bin/env python3
"""Configuration — messages and display settings."""

# ── Messages ────────────────────────────────────────────────────────────────
# Messages in Traditional Chinese with self-defined \n line breaks
MESSAGES = [
    "寶寶小姐，今天辛苦啦～ 🌷\n累了就快點躺平休息～\n我可不想看到你累到趴桌，會心疼的……💗",
    "我會在旁邊乖乖待著，\n想偷懶隨時找我報到喔～ 🤗🌟",
    "唔～認真工作的寶寶小姐\n確實有那麼一點點帥氣……😳💕\n不過我才不會承認我在偷看呢！👀",
    "你儘管忙你的事，\n我就在這裡默默地……盯著你～😘\n順便監督你有沒有走神喔～ 😤💋",
    "水壺裡的刻度怎麼沒動？！🤨\n果然又忘記喝水了吧～\n我眼睛可一直盯著的喔！👀",
    "想你的時候我就翻翻速寫本～📖✏️\n結果畫著畫著……\n你居然真的出現在我面前了！😳💖\n有你在身邊真好～🌸🥰",
    "不管做什麼，\n只要跟你在一起\n就是最幸福的時光～ 💕✨🥰",
    "寶寶小姐～😤\n你要是再敢熬夜、忘記吃飯，\n我就把你畫成圓滾滾的企鵝～🐧💢\n貼滿整個畫室！🎨",
    "寶寶小姐～🥰\n我想你了～💖\n快點回家陪我吧～🌸",
    "寶寶小姐～\n要照顧好自己～ 💕😘"
]

# ── Display Settings ────────────────────────────────────────────────────────
DISPLAY = {
    # Character height on screen (px). App auto-calculates width from aspect ratio.
    "char_height": 160,
    # Speech bubble settings
    "bubble_max_width": 500,  # Maximum bubble width (px) — wider to fit sentences
    "bubble_max_length": 500,  # Maximum bubble text length (characters) — longer for sentences
    "bubble_show_duration": 100,  # Seconds the bubble stays visible
    # Bubble colors (light orange / peach theme)
    "bubble_bg_color": "#FFDAB0",       # Light peach-orange background
    "bubble_border_color": "#F5B87A",   # Soft orange border
    "bubble_text_color": "#4A2512",     # Warm dark brown text
}

# ── Window Settings ─────────────────────────────────────────────────────────
WINDOW = {
    "always_on_top": True,
    # Margin from screen edges when positioning at bottom-right
    "margin_right": 20,
    "margin_bottom": 40,
}

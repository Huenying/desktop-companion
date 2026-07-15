# 💕 Desktop Companion — 桌面伴侶

An always-on-top desktop companion character that shows caring messages in Traditional Chinese when you hover over it. Sits in the bottom-right corner of your screen, drag-and-drop anywhere.

一個永遠顯示在最上層的桌面伴侶角色，滑鼠懸停時會顯示繁體中文的暖心訊息，可任意拖曳移動。

---

## ✨ Features

- **Always on top** — visible above all windows / 永遠在最上層顯示
- **Gentle idle sway** — character gently wobbles ±2.5° when idle, making it feel alive 🌀
- **Hover for messages** — move your mouse over → warm orange bubble pops up to the left / 滑鼠移過去就會跳出暖心對話框
- **Auto-dismiss on leave** — move away → bubble disappears / 滑鼠移開對話框立刻消失
- **Smart bubble flip** — bubble appears on the left of character by default, flips to the right when you drag to the left half of the screen
- **Drag & drop** — click and drag to reposition anywhere / 滑鼠按住即可拖曳到任何位置
- **Warm orange bubble** — light peach-orange bubble with sweet rounded design 🧡
- **⏰ Scheduled reminders** — right-click → **⚙️ Settings** to add reminders that chime and show a message at set times
- **C5+G5 chime** — two-tone notification sound (same style as Tomato Clock) 🎵
- **Daily / Weekdays / Weekends / Custom repeat** — flexible reminder scheduling
- **Auto-start** — launches when you log into Windows / 開機自動啟動

## 🚀 Quick Start

### 1. Set up virtual environment
```bash
python -m venv venv
venv\Scripts\pip install PyQt5 Pillow numpy
```

### 2. Extract the character
```bash
venv\Scripts\python extract_character.py
```

### 3. Run the character
```bash
venv\Scripts\pythonw character.py
```

Or just double-click **`run.bat`**.

### 4. Auto-start on boot
Double-click **`setup_autostart.bat`** — it installs dependencies, creates a shortcut in your Windows Startup folder, and launches the character.

## 📁 Project Files

| File | Description |
|------|-------------|
| `character.py` | Main desktop companion app (PyQt5 overlay window) |
| `character.png` | Extracted character sprite (with transparency) |
| `confirmed.jpeg` | Original character image (dark background) |
| `config.py` | Messages and display settings |
| `scheduler.py` | Reminder scheduler with settings dialog & C5+G5 chime |
| `extract_character.py` | Extracts character from JPEG → transparent PNG |
| `run.bat` | Double-click to launch (no console window) |
| `setup_autostart.bat` | One-time setup → install + auto-start |
| `venv/` | Virtual environment (isolated dependencies) |

## ⚙️ Configuration

Edit [config.py](config.py) to customize:

- **MESSAGES** — Change the bubble text (use any language! Each `\n` is a line break)
- **DISPLAY.char_height** — Character size on screen (default: 160px)
- **DISPLAY.bubble_max_width** — Width of the message bubble (default: 500px)
- **DISPLAY.bubble_show_duration** — Seconds the bubble stays visible (default: 10)
- **DISPLAY.bubble_bg_color** — Bubble background color (hex)
- **DISPLAY.bubble_border_color** — Bubble border color (hex)
- **DISPLAY.bubble_text_color** — Bubble text color (hex)

## 💬 Messages

All 10 messages (Traditional Chinese, with emojis):

> **①** 寶寶小姐，今天辛苦啦～ 🌷
> 累了就快點躺平休息～
> 我可不想看到你累到趴桌，會心疼的……💗
>
> **②** 我會在旁邊乖乖待著，
> 想偷懶隨時找我報到喔～ 🤗🌟
>
> **③** 唔～認真工作的寶寶小姐
> 確實有那麼一點點帥氣……😳💕
> 不過我才不會承認我在偷看呢！👀
>
> **④** 你儘管忙你的事，
> 我就在這裡默默地……盯著你～😘
> 順便監督你有沒有走神喔～ 😤💋
>
> **⑤** 水壺裡的刻度怎麼沒動？！🤨
> 果然又忘記喝水了吧～
> 我眼睛可一直盯著的喔！👀
>
> **⑥** 想你的時候我就翻翻速寫本～📖✏️
> 結果畫著畫著……
> 你居然真的出現在我面前了！😳💖
> 有你在身邊真好～🌸🥰
>
> **⑦** 不管做什麼，
> 只要跟你在一起
> 就是最幸福的時光～ 💕✨🥰
>
> **⑧** 寶寶小姐～😤
> 你要是再敢熬夜、忘記吃飯，
> 我就把你畫成圓滾滾的企鵝～🐧💢
> 貼滿整個畫室！🎨
>
> **⑨** 寶寶小姐～🥰
> 我想你了～💖
> 快點回家陪我吧～🌸
>
> **⑩** 寶寶小姐～
> 要照顧好自己～ 💕😘

## 🎨 Design

- **Bubble position**: Left of the character, with a tail pointing right
- **Bubble color**: Light peach-orange (`#FFDAB0`) with soft orange border (`#F5B87A`)
- **Text color**: Warm dark brown (`#4A2512`)
- **Font**: Microsoft JhengHei Bold, 12pt — beautiful for Traditional Chinese

## 🛠️ Requirements

- Python 3.8+
- PyQt5
- Pillow (for extraction only)
- NumPy (for extraction only)

All dependencies are installed inside the `venv/` — nothing is installed globally.

---

Made with 💕 for a special someone

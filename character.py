#!/usr/bin/env python3
"""
Desktop Companion Character
━━━━━━━━━━━━━━━━━━━━━━━━━━━
An always-on-top transparent overlay that sits on your desktop.
A cute boyfriend character with warm orange message bubbles.
Messages appear to the LEFT of the character when you hover.

Requirements: PyQt5
"""

import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QMenu
from PyQt5.QtCore import Qt, QTimer, QRect, QRectF, QPoint
from PyQt5.QtGui import QPainter, QPixmap, QColor, QFont, QFontMetrics, \
    QPainterPath, QPen

from config import MESSAGES, DISPLAY, WINDOW


# ═════════════════════════════════════════════════════════════════════════════
#  Color helpers
# ═════════════════════════════════════════════════════════════════════════════

def _hex_color(h):
    """'#RRGGBB' -> QColor"""
    return QColor(h)


# ═════════════════════════════════════════════════════════════════════════════
#  Main widget
# ═════════════════════════════════════════════════════════════════════════════

class CharacterWidget(QWidget):
    """Frameless, transparent, always-on-top companion character."""

    def __init__(self):
        super().__init__()

        # ── Load image ──────────────────────────────────────────────────
        self.char_pixmap = QPixmap("character.png")
        if self.char_pixmap.isNull():
            raise FileNotFoundError(
                "character.png not found — run extract_character.py first"
            )

        orig_w = self.char_pixmap.width()
        orig_h = self.char_pixmap.height()
        scale = DISPLAY["char_height"] / orig_h
        self.char_display_w = int(orig_w * scale)
        self.char_display_h = DISPLAY["char_height"]

        # Pre-scale once for performance
        self.char_scaled = self.char_pixmap.scaled(
            self.char_display_w,
            self.char_display_h,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        # ── Layout geometry ─────────────────────────────────────────────
        self.bubble_max_w = DISPLAY["bubble_max_width"]
        self.bubble_show_ms = DISPLAY["bubble_show_duration"] * 1000
        self.bubble_pad = 14
        self.bubble_radius = 16
        self.bubble_tail_w = 14
        self.bubble_tail_h = 10
        self.gap = 12              # gap between bubble right edge and character
        self.pad = 12              # outer padding

        # Colors
        self.bubble_bg = _hex_color(DISPLAY["bubble_bg_color"])
        self.bubble_border = _hex_color(DISPLAY["bubble_border_color"])
        self.text_color = _hex_color(DISPLAY["bubble_text_color"])

        # Window size — wide enough for bubble + gap + character
        # Height must fit whichever is taller: the character or the bubble
        self.win_w = self.pad + self.bubble_max_w + self.gap \
                     + self.char_display_w + self.pad
        est_bubble_h = 250  # tall enough for long messages + padding
        self.win_h = max(self.char_display_h, est_bubble_h) + self.pad * 2
        self.setFixedSize(self.win_w, self.win_h)

        # Character position (right side, vertically centered)
        self.char_x = self.win_w - self.pad - self.char_display_w
        self.char_y = (self.win_h - self.char_display_h) // 2
        self.char_rect = QRect(self.char_x, self.char_y,
                               self.char_display_w, self.char_display_h)

        # ── State ───────────────────────────────────────────────────────
        self.current_message = ""
        self.bubble_visible = False
        self.dragging = False
        self.drag_offset = QPoint()

        # ── Window flags ────────────────────────────────────────────────
        flags = Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self._position_bottom_right()

        # ── Timers ──────────────────────────────────────────────────────
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._hide_bubble)

        # ── Right-click menu ────────────────────────────────────────────
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

    # ── Window positioning ─────────────────────────────────────────────────

    def _position_bottom_right(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - self.win_w - WINDOW["margin_right"]
        y = screen.bottom() - self.win_h - WINDOW["margin_bottom"]
        self.move(x, y)

    # ── Bubble control ─────────────────────────────────────────────────────

    def _show_bubble(self, message):
        self.current_message = message
        self.bubble_visible = True
        self.hide_timer.start(self.bubble_show_ms)
        self.update()

    def _hide_bubble(self):
        self.bubble_visible = False
        self.update()

    def _show_random_message(self):
        choices = [m for m in MESSAGES if m != self.current_message]
        msg = random.choice(choices) if choices else random.choice(MESSAGES)
        self._show_bubble(msg)

    # ── Hover → bubble ─────────────────────────────────────────────────────

    def enterEvent(self, event):
        self._show_random_message()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hide_bubble()
        super().leaveEvent(event)

    # ── Drag & drop ────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.mapToGlobal(event.pos() - self.drag_offset))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    # ── Context menu ───────────────────────────────────────────────────────

    def _context_menu(self, pos):
        menu = QMenu()

        show_act = menu.addAction(
            "Hide Message" if self.bubble_visible else "Show Message"
        )
        show_act.triggered.connect(self._toggle_bubble)
        menu.addSeparator()

        reset = menu.addAction("Reset Position")
        reset.triggered.connect(self._position_bottom_right)
        menu.addSeparator()

        ex = menu.addAction("Exit")
        ex.triggered.connect(QApplication.instance().quit)
        menu.exec_(self.mapToGlobal(pos))

    def _toggle_bubble(self):
        if self.bubble_visible:
            self._hide_bubble()
        else:
            self._show_random_message()

    # ── Painting ───────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        # ── Character (paint first so bubble paints on top if overlapping) ─
        painter.drawPixmap(self.char_rect, self.char_scaled)

        # ── Bubble (to the left of the character) ──────────────────────────
        if self.bubble_visible and self.current_message:
            # Font — sweet & readable for Chinese
            font = QFont("Microsoft JhengHei", 12, QFont.Bold)
            painter.setFont(font)
            fm = QFontMetrics(font)

            # Wrap text: respect \n breaks, then character-wrap overflow
            max_text_w = self.bubble_max_w - self.bubble_pad * 2
            segments = self.current_message.split("\n")
            lines = []
            for seg in segments:
                if not seg:
                    lines.append("")   # preserve blank lines
                elif fm.horizontalAdvance(seg) <= max_text_w:
                    lines.append(seg)
                else:
                    line = ""
                    for ch in seg:
                        test = line + ch
                        if fm.horizontalAdvance(test) <= max_text_w:
                            line = test
                        else:
                            if line:
                                lines.append(line)
                            line = ch
                    if line:
                        lines.append(line)

            line_h = fm.height() + 4
            # Filter out empty lines for height calc but keep for vertical spacing
            non_empty = [l for l in lines if l]
            text_h = len(non_empty) * line_h + lines.count("") * (line_h // 2)
            content_h = text_h + self.bubble_pad * 2
            total_h = content_h + self.bubble_tail_h

            # Bubble width = max line width
            line_widths = [fm.horizontalAdvance(l) for l in non_empty] or [60]
            bubble_w = min(
                self.bubble_max_w,
                max(line_widths) + self.bubble_pad * 2 + 24,
            )

            # Position bubble to the LEFT of the character
            bx = self.char_x - self.gap - bubble_w
            # Vertically center bubble relative to character
            by = self.char_y + (self.char_display_h - total_h) // 2
            # Clamp so it doesn't go off-screen top/bottom
            by = max(self.pad, by)
            if by + total_h > self.win_h - self.pad:
                by = self.win_h - self.pad - total_h

            body_rect = QRectF(bx, by, bubble_w, content_h)

            # ── Shadow ──
            shadow_off = 3
            spath = QPainterPath()
            spath.addRoundedRect(
                body_rect.translated(shadow_off, shadow_off),
                self.bubble_radius, self.bubble_radius,
            )
            painter.fillPath(spath, QColor(0, 0, 0, 35))

            # ── Bubble body (warm orange) ──
            path = QPainterPath()
            path.addRoundedRect(body_rect, self.bubble_radius, self.bubble_radius)
            painter.fillPath(path, self.bubble_bg)
            painter.setPen(QPen(self.bubble_border, 1.5))
            painter.drawPath(path)

            # ── Tail (pointing RIGHT toward character) ──
            # Tail triangle emerges from the right edge of the bubble
            ty = body_rect.center().y()
            tx = body_rect.right()
            tail = QPainterPath()
            tail.moveTo(tx, ty - self.bubble_tail_h)
            tail.lineTo(tx + self.bubble_tail_w, ty)
            tail.lineTo(tx, ty + self.bubble_tail_h)
            tail.closeSubpath()
            painter.fillPath(tail, self.bubble_bg)
            painter.setPen(QPen(self.bubble_border, 1.5))
            painter.drawPath(tail)

            # ── Text (warm brown) ──
            tx = int(bx + self.bubble_pad)
            ty2 = int(by + self.bubble_pad + fm.ascent() + 1)
            painter.setPen(self.text_color)
            for line in lines:
                if line:
                    painter.drawText(tx, ty2, line)
                    ty2 += line_h
                else:
                    ty2 += line_h // 2   # blank line = half spacing
                    ty2 += line_h // 2


# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Desktop Companion")

    try:
        w = CharacterWidget()
        w.show()
        sys.exit(app.exec_())
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        input("Press Enter to exit...")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)

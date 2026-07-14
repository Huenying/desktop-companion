#!/usr/bin/env python3
"""
Reminder scheduler for Desktop Companion.
──────────────────────────────
Stores reminders in a JSON file, checks them every 30 seconds,
plays a C5+E5 chime (same as Tomato Clock) and shows the message
bubble when a reminder fires.

Double-click the character → opens the Settings dialog.
"""

import json
import os
import struct
import tempfile
import ctypes
import winsound
import math
from datetime import datetime, date, time as dtime
from dataclasses import dataclass, asdict
from typing import List, Optional, Callable

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QTimeEdit, QComboBox, QHeaderView,
    QMessageBox, QGroupBox, QCheckBox, QFormLayout, QAbstractItemView,
)
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QFont

# ── File path ───────────────────────────────────────────────────────────────
REMINDERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminders.json")


# ═════════════════════════════════════════════════════════════════════════════
#  C5+E5 chime — same sound as Tomato Clock
# ═════════════════════════════════════════════════════════════════════════════

_CHIME_CACHE = None  # cache the WAV bytes

def _generate_chime_wav() -> bytes:
    """Generate a WAV file with C5 (523.25 Hz) + G5 (783.99 Hz) chime.

    Two-tone chime:
      - C5 at t=0s, decays over 0.5s
      - G5 at t=0.15s, decays over 0.5s
      - Combined into a single 16-bit mono WAV
    """
    sample_rate = 22050
    duration = 0.7        # total duration (s)
    num_samples = int(sample_rate * duration)

    c5_freq = 523.25
    g5_freq = 783.99

    samples = []
    for i in range(num_samples):
        t = i / sample_rate

        # C5 starts at t=0, decays exponentially
        c5_amp = math.exp(-2.0 * t) if t < 0.5 else 0.0
        c5_val = math.sin(2.0 * math.pi * c5_freq * t) * c5_amp

        # G5 starts at t=0.15, decays exponentially
        g5_t = t - 0.15
        g5_amp = math.exp(-2.0 * g5_t) if 0 <= g5_t < 0.5 else 0.0
        g5_val = math.sin(2.0 * math.pi * g5_freq * t) * g5_amp if g5_t >= 0 else 0.0

        # Mix and scale to 16-bit
        val = int((c5_val + g5_val) * 0.5 * 28000)
        val = max(-32768, min(32767, val))
        samples.append(val)

    # Build WAV file in memory
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = num_samples * block_align

    wav = b"RIFF"
    wav += struct.pack("<I", 36 + data_size)
    wav += b"WAVE"
    wav += b"fmt "
    wav += struct.pack("<IHHIIHH", 16, 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample)
    wav += b"data"
    wav += struct.pack("<I", data_size)
    for s in samples:
        wav += struct.pack("<h", s)

    return wav


def play_chime():
    """Play the C5+E5 chime sound."""
    global _CHIME_CACHE
    if _CHIME_CACHE is None:
        _CHIME_CACHE = _generate_chime_wav()

    # Write to a temp file and play it
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.write(_CHIME_CACHE)
        tmp.close()
        winsound.PlaySound(tmp.name, winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        # Schedule deletion after sound plays (approximate)
        QTimer.singleShot(1500, lambda: os.unlink(tmp.name) if os.path.exists(tmp.name) else None)
    except Exception:
        # Fallback: simple beep
        try:
            winsound.Beep(523, 150)
        except Exception:
            pass


# ═════════════════════════════════════════════════════════════════════════════
#  Data model
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class Reminder:
    time_str: str           # "HH:MM" in 24-hour format
    message: str            # The message to show
    repeat: str             # "daily", "weekdays", "weekends", "custom"
    days: List[int] = None  # 0=Mon..6=Sun — only used if repeat="custom"

    def matches_today(self) -> bool:
        today = date.today().weekday()
        if self.repeat == "daily":
            return True
        if self.repeat == "weekdays":
            return today < 5
        if self.repeat == "weekends":
            return today >= 5
        if self.repeat == "custom" and self.days:
            return today in self.days
        return False

    def matches_time(self, t: dtime) -> bool:
        parts = self.time_str.split(":")
        h, m = int(parts[0]), int(parts[1])
        return t.hour == h and t.minute == m


# ═════════════════════════════════════════════════════════════════════════════
#  Storage
# ═════════════════════════════════════════════════════════════════════════════

def load_reminders() -> List[Reminder]:
    if not os.path.exists(REMINDERS_FILE):
        return []
    try:
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Reminder(**r) for r in data]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def save_reminders(reminders: List[Reminder]):
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in reminders], f, ensure_ascii=False, indent=2)


# ═════════════════════════════════════════════════════════════════════════════
#  Reminder edit dialog
# ═════════════════════════════════════════════════════════════════════════════

class ReminderEditDialog(QDialog):
    """Dialog to add or edit one reminder."""

    def __init__(self, reminder: Optional[Reminder] = None, parent=None):
        super().__init__(parent)
        self.reminder = reminder
        self.setWindowTitle("Edit Reminder" if reminder else "Add Reminder")
        self.setFixedSize(480, 360)

        # Same warm orange title bar and no icon as parent SettingsDialog
        _make_dialog_iconless(self)
        _set_window_titlebar_color(self.winId(), 255, 218, 176)

        self.setStyleSheet("""
            QDialog {
                background-color: #FFDAB0;
            }
            QGroupBox {
                background-color: #FFE8C8;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #F5B87A;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F0A86A;
            }
            QLineEdit, QTimeEdit, QComboBox {
                background-color: #FFF5E6;
                border: 1px solid #F5B87A;
                border-radius: 4px;
                padding: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ── Time ──
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("⏰ Time:"))
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        if reminder:
            parts = reminder.time_str.split(":")
            self.time_edit.setTime(QTime(int(parts[0]), int(parts[1])))
        else:
            self.time_edit.setTime(QTime(12, 0))
        self.time_edit.setFont(QFont("Segoe UI", 11))
        time_layout.addWidget(self.time_edit)
        time_layout.addStretch()
        layout.addLayout(time_layout)

        # ── Message ──
        msg_layout = QVBoxLayout()
        msg_layout.addWidget(QLabel("💬 Message:"))
        self.message_edit = QLineEdit()
        self.message_edit.setPlaceholderText("")
        self.message_edit.setFont(QFont("Microsoft JhengHei", 11))
        if reminder:
            self.message_edit.setText(reminder.message)
        msg_layout.addWidget(self.message_edit)
        layout.addLayout(msg_layout)

        # ── Repeat ──
        repeat_layout = QFormLayout()
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(["Daily", "Weekdays (Mon-Fri)", "Weekends (Sat-Sun)", "Custom days..."])
        self.repeat_combo.currentIndexChanged.connect(self._on_repeat_changed)
        if reminder:
            idx_map = {"daily": 0, "weekdays": 1, "weekends": 2, "custom": 3}
            self.repeat_combo.setCurrentIndex(idx_map.get(reminder.repeat, 0))
        repeat_layout.addRow("🔄 Repeat:", self.repeat_combo)
        layout.addLayout(repeat_layout)

        # ── Custom day checkboxes (2 rows: 4 + 3) ──
        self.day_group = QGroupBox("  Select days:")
        day_layout = QVBoxLayout()
        day_layout.setContentsMargins(14, 24, 14, 14)
        day_grid1 = QHBoxLayout()
        day_grid1.setSpacing(12)
        day_grid2 = QHBoxLayout()
        day_grid2.setSpacing(12)
        self.day_checks = []
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, name in enumerate(day_names):
            cb = QCheckBox(name)
            if reminder and reminder.days and i in reminder.days:
                cb.setChecked(True)
            self.day_checks.append(cb)
            if i < 4:
                day_grid1.addWidget(cb)
            else:
                day_grid2.addWidget(cb)
        day_layout.addLayout(day_grid1)
        day_layout.addLayout(day_grid2)
        self.day_group.setLayout(day_layout)
        self.day_group.setVisible(self.repeat_combo.currentIndex() == 3)
        layout.addWidget(self.day_group)

        layout.addStretch()

        # ── Buttons ──
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("✅ Save")
        save_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _on_repeat_changed(self, idx):
        self.day_group.setVisible(idx == 3)

    def _save(self):
        msg = self.message_edit.text().strip()
        if not msg:
            warn = QMessageBox(QMessageBox.Warning, "Oops", "Please enter a message!", parent=self)
            warn.setStyleSheet("QMessageBox { background-color: #FFDAB0; } QPushButton { background-color: #F5B87A; border: none; border-radius: 4px; padding: 4px 12px; }")
            warn.exec_()
            return

        t = self.time_edit.time()
        time_str = f"{t.hour():02d}:{t.minute():02d}"

        idx = self.repeat_combo.currentIndex()
        repeat_map = {0: "daily", 1: "weekdays", 2: "weekends", 3: "custom"}
        repeat = repeat_map[idx]

        days = None
        if repeat == "custom":
            days = [i for i, cb in enumerate(self.day_checks) if cb.isChecked()]
            if not days:
                warn = QMessageBox(QMessageBox.Warning, "Oops", "Please select at least one day!", parent=self)
                warn.setStyleSheet("QMessageBox { background-color: #FFDAB0; } QPushButton { background-color: #F5B87A; border: none; border-radius: 4px; padding: 4px 12px; }")
                warn.exec_()
                return

        self.reminder = Reminder(time_str=time_str, message=msg, repeat=repeat, days=days)
        self.accept()


# ═════════════════════════════════════════════════════════════════════════════
#  Settings dialog
# ═════════════════════════════════════════════════════════════════════════════

def _set_window_titlebar_color(win_id, r, g, b):
    """Set the Windows title bar color via DWM API (Windows 10/11)."""
    try:
        # DWMWA_CAPTION_COLOR = 35 (Windows 10 20H1+)
        DWMWA_CAPTION_COLOR = 35
        # Color in BGR format (0x00BBGGRR)
        color = (r & 0xFF) | ((g & 0xFF) << 8) | ((b & 0xFF) << 16)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            int(win_id), DWMWA_CAPTION_COLOR,
            ctypes.byref(ctypes.c_int(color)), ctypes.sizeof(ctypes.c_int)
        )
    except Exception:
        pass  # DWM not available or unsupported


def _make_dialog_iconless(dlg):
    """Remove the icon from a QDialog title bar using window flags.

    Removes WS_SYSMENU but re-adds close/minimize/maximize buttons
    via separate window hints, so the icon disappears but buttons remain.
    """
    try:
        dlg.setWindowFlags(
            Qt.Dialog
            | Qt.WindowTitleHint
            | Qt.WindowCloseButtonHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.CustomizeWindowHint
        )
    except Exception:
        pass


class SettingsDialog(QDialog):
    """Main settings window with a table of reminders."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.reminders = load_reminders()
        self.setWindowTitle("⏰ Reminder Settings")
        self.setFixedSize(640, 480)

        # Remove the default icon from the title bar (must be before DWM color,
        # because setWindowFlags recreates the native window)
        _make_dialog_iconless(self)
        # Set warm orange title bar via DWM
        _set_window_titlebar_color(self.winId(), 255, 218, 176)

        self.setStyleSheet("""
            QDialog {
                background-color: #FFDAB0;
            }
            QGroupBox {
                background-color: #FFE8C8;
                border-radius: 8px;
                font-weight: bold;
            }
            QTableWidget {
                background-color: #FFF5E6;
                border-radius: 6px;
            }
            QPushButton {
                background-color: #F5B87A;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F0A86A;
            }
            QLineEdit, QTimeEdit, QComboBox {
                background-color: #FFF5E6;
                border: 1px solid #F5B87A;
                border-radius: 4px;
                padding: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("⏰ Notification Reminders")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)

        subtitle = QLabel("Set times when the character will chime and show a bubble message.")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        # ── Table ──
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Time", "Message", "Repeat"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit_reminder)
        self._populate_table()
        layout.addWidget(self.table)

        # ── Buttons ──
        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ Add")
        add_btn.clicked.connect(self._add_reminder)
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.clicked.connect(self._edit_selected)
        del_btn = QPushButton("🗑️ Delete")
        del_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()

        close_btn = QPushButton("✅ Done")
        close_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        close_btn.clicked.connect(self._close_and_save)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _populate_table(self):
        self.table.setRowCount(len(self.reminders))
        for i, r in enumerate(self.reminders):
            self.table.setItem(i, 0, QTableWidgetItem(r.time_str))
            self.table.setItem(i, 1, QTableWidgetItem(r.message))
            label_map = {"daily": "Daily", "weekdays": "Weekdays",
                         "weekends": "Weekends", "custom": "Custom"}
            self.table.setItem(i, 2, QTableWidgetItem(label_map.get(r.repeat, r.repeat)))

    def _get_selected_row(self) -> int:
        rows = set(i.row() for i in self.table.selectedIndexes())
        return rows.pop() if rows else -1

    def _add_reminder(self):
        dlg = ReminderEditDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted and dlg.reminder:
            self.reminders.append(dlg.reminder)
            self._populate_table()

    def _edit_reminder(self, index):
        row = index.row()
        dlg = ReminderEditDialog(reminder=self.reminders[row], parent=self)
        if dlg.exec_() == QDialog.Accepted and dlg.reminder:
            self.reminders[row] = dlg.reminder
            self._populate_table()

    def _edit_selected(self):
        row = self._get_selected_row()
        if row >= 0:
            dlg = ReminderEditDialog(reminder=self.reminders[row], parent=self)
            if dlg.exec_() == QDialog.Accepted and dlg.reminder:
                self.reminders[row] = dlg.reminder
                self._populate_table()

    def _delete_selected(self):
        row = self._get_selected_row()
        if row >= 0:
            r = self.reminders[row]
            confirm_box = QMessageBox(
                QMessageBox.Question, "Delete?",
                f'Delete reminder "{r.message}" at {r.time_str}?',
                QMessageBox.Yes | QMessageBox.No, parent=self,
            )
            confirm_box.setStyleSheet("""
                QMessageBox { background-color: #FFDAB0; }
                QPushButton { background-color: #F5B87A; border: none; border-radius: 4px; padding: 4px 12px; min-width: 60px; }
                QPushButton:hover { background-color: #F0A86A; }
                QLabel { color: #4A2512; font-size: 11pt; }
            """)
            result = confirm_box.exec_()
            if result == QMessageBox.Yes:
                del self.reminders[row]
                self._populate_table()

    def _close_and_save(self):
        save_reminders(self.reminders)
        self.accept()


# ═════════════════════════════════════════════════════════════════════════════
#  Scheduler (background checker)
# ═════════════════════════════════════════════════════════════════════════════

class ReminderScheduler:
    """Checks reminders every 30 seconds and fires notifications."""

    def __init__(self, show_bubble_callback: Callable[[str], None], parent):
        """
        show_bubble_callback: function(message) to display the bubble
        parent: QObject for timer ownership
        """
        self.show_bubble = show_bubble_callback
        self._fired_today: set = set()
        self._last_date_str = date.today().isoformat()

        self.timer = QTimer(parent)
        self.timer.timeout.connect(self._check)
        self.timer.start(30_000)

    def _check(self):
        today_str = date.today().isoformat()
        if today_str != self._last_date_str:
            self._fired_today.clear()
            self._last_date_str = today_str

        now = datetime.now().time()
        reminders = load_reminders()
        for r in reminders:
            key = (r.time_str, r.message, today_str)
            if key not in self._fired_today and r.matches_today() and r.matches_time(now):
                self._fired_today.add(key)
                play_chime()
                self.show_bubble(r.message)

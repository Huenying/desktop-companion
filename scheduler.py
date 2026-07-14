#!/usr/bin/env python3
"""
Reminder scheduler and settings dialog for Desktop Companion.
Stores reminders in reminders.json, checks them every 30 seconds,
plays a notification sound and shows the message bubble when a reminder fires.
"""

import json
import os
import winsound
from datetime import datetime, date, time as dtime
from dataclasses import dataclass, asdict
from typing import List, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QTimeEdit, QComboBox, QHeaderView,
    QMessageBox, QWidget, QGroupBox, QCheckBox, QFormLayout, QAbstractItemView,
)
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QFont

# ── File path for storing reminders ─────────────────────────────────────────
REMINDERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminders.json")


# ═════════════════════════════════════════════════════════════════════════════
#  Data model
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class Reminder:
    time_str: str           # "HH:MM" in 24-hour format
    message: str            # The message to show
    repeat: str             # "daily", "weekdays", "weekends"
    days: List[int] = None  # Specific days of week (0=Mon..6=Sun) — only used if repeat="custom"

    def matches_today(self) -> bool:
        """Does this reminder fire today?"""
        today = date.today().weekday()  # 0=Mon .. 6=Sun
        if self.repeat == "daily":
            return True
        if self.repeat == "weekdays":
            return today < 5  # Mon-Fri
        if self.repeat == "weekends":
            return today >= 5  # Sat-Sun
        if self.repeat == "custom" and self.days:
            return today in self.days
        return False

    def matches_time(self, t: dtime) -> bool:
        """Does this reminder fire at the given time? (minute precision)"""
        parts = self.time_str.split(":")
        h, m = int(parts[0]), int(parts[1])
        return t.hour == h and t.minute == m


# ═════════════════════════════════════════════════════════════════════════════
#  Storage
# ═════════════════════════════════════════════════════════════════════════════

def load_reminders() -> List[Reminder]:
    """Load reminders from JSON file."""
    if not os.path.exists(REMINDERS_FILE):
        return []
    try:
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Reminder(**r) for r in data]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def save_reminders(reminders: List[Reminder]):
    """Save reminders to JSON file."""
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in reminders], f, ensure_ascii=False, indent=2)


# ═════════════════════════════════════════════════════════════════════════════
#  Edit dialog (single reminder)
# ═════════════════════════════════════════════════════════════════════════════

class ReminderEditDialog(QDialog):
    """Dialog to add or edit one reminder."""

    def __init__(self, reminder: Optional[Reminder] = None, parent=None):
        super().__init__(parent)
        self.reminder = reminder
        self.setWindowTitle("Edit Reminder" if reminder else "Add Reminder")
        self.setFixedSize(380, 280)

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
        self.message_edit.setPlaceholderText("e.g. 吃飯啦～ 🍱")
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

        # ── Custom day checkboxes ──
        self.day_group = QGroupBox("Select days:")
        day_grid = QHBoxLayout()
        self.day_checks = []
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, name in enumerate(day_names):
            cb = QCheckBox(name)
            if reminder and reminder.days and i in reminder.days:
                cb.setChecked(True)
            self.day_checks.append(cb)
            day_grid.addWidget(cb)
        self.day_group.setLayout(day_grid)
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
            QMessageBox.warning(self, "Oops", "Please enter a message!")
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
                QMessageBox.warning(self, "Oops", "Please select at least one day!")
                return

        self.reminder = Reminder(time_str=time_str, message=msg, repeat=repeat, days=days)
        self.accept()


# ═════════════════════════════════════════════════════════════════════════════
#  Settings dialog (list of reminders)
# ═════════════════════════════════════════════════════════════════════════════

class SettingsDialog(QDialog):
    """Main settings window with a table of reminders."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.reminders = load_reminders()
        self.setWindowTitle("⚙️ Reminder Settings")
        self.setFixedSize(550, 400)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("⏰ Notification Reminders")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)

        subtitle = QLabel("Set times when the character will ring a notification\nand show a custom message.")
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

    # ── Table helpers ───────────────────────────────────────────────────────

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

    # ── Actions ─────────────────────────────────────────────────────────────

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
            confirm = QMessageBox.question(
                self, "Delete?", f'Delete reminder "{r.message}" at {r.time_str}?',
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirm == QMessageBox.Yes:
                del self.reminders[row]
                self._populate_table()

    def _close_and_save(self):
        save_reminders(self.reminders)
        self.accept()


# ═════════════════════════════════════════════════════════════════════════════
#  Scheduler (runs in the background)
# ═════════════════════════════════════════════════════════════════════════════

class ReminderScheduler:
    """Checks reminders every 30 seconds and fires notifications."""

    def __init__(self, show_bubble_callback, parent):
        """
        show_bubble_callback: function(message) to show the bubble
        parent: QObject for timer ownership
        """
        self.show_bubble = show_bubble_callback
        self._fired_today: set = set()  # Track which reminders fired today
        self._last_date_str = date.today().isoformat()

        self.timer = QTimer(parent)
        self.timer.timeout.connect(self._check)
        self.timer.start(30_000)  # every 30 seconds

    def _check(self):
        """Check if any reminder should fire now."""
        # Reset fired set if date changed
        today_str = date.today().isoformat()
        if today_str != self._last_date_str:
            self._fired_today.clear()
            self._last_date_str = today_str

        now = datetime.now().time()

        reminders = load_reminders()
        for r in reminders:
            # Create a unique key for this reminder + date
            key = (r.time_str, r.message, today_str)

            if key not in self._fired_today and r.matches_today() and r.matches_time(now):
                # Fire!
                self._fired_today.add(key)

                # Play notification sound (Tomato Clock chime: C5 + E5)
                try:
                    import threading
                    def _play_chime():
                        # C5 (523.25 Hz) then E5 (659.25 Hz) — major third
                        winsound.Beep(523, 200)  # C5, 200ms
                        import time; time.sleep(0.1)
                        winsound.Beep(659, 200)  # E5, 200ms
                    threading.Thread(target=_play_chime, daemon=True).start()
                except:
                    pass

                # Show the message
                self.show_bubble(r.message)

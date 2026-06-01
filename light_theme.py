"""Light theme styles and utilities.

This module provides a LightThemeMixin and helper functions for
producing consistent widget styles. It avoids duplicating toggle
button CSS by using a small generator function.
"""

import sys
from PySide6.QtCore import Qt, QPointF, QRectF, QUrl, QEvent, QTimer
from PySide6.QtGui import QPixmap, QPainter, QImage, QColor, QLinearGradient, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect
try:
    from PySide6.QtGui import QSurfaceFormat
except Exception:
    QSurfaceFormat = None

# Constants
ICON_SIZE = 36
AUTHOR_FONT_SIZE = 10

def toggle_btn_style(active: bool, left: bool, dark: bool) -> str:
    """Return stylesheet for a toggle button.

    Parameters:
        active: whether this half is active/on
        left: whether this is the left half (affects corner radii)
        dark: whether dark theme colors should be used
    """
    if dark:
        bg = "#232323" if active else "#444"
        fg = "#fff" if active else "#888"
        border = "#2a2a2a"
    else:
        bg = "#fff" if active else "#e0e0e0"
        fg = "#232323" if active else "#888"
        border = "#e0e0e0" if active else "#d6d6d6"
    radius_left = "8px" if left else "0px"
    radius_right = "8px" if not left else "0px"
    font_weight = "bold" if active else "normal"
    return f"""
        QPushButton {{
            background: {bg};
            color: {fg};
            border: 1px solid {border};
            border-top-left-radius: {radius_left};
            border-bottom-left-radius: {radius_left};
            border-top-right-radius: {radius_right};
            border-bottom-right-radius: {radius_right};
            font-weight: {font_weight};
        }}
    """

# Backwards-compatible wrappers (old API)
def toggle_active_style():
    return toggle_btn_style(active=True, left=False, dark=False)

def toggle_inactive_style():
    return toggle_btn_style(active=False, left=False, dark=False)

def toggle_active_left_style():
    return toggle_btn_style(active=True, left=True, dark=False)

def toggle_active_right_style():
    return toggle_btn_style(active=True, left=False, dark=False)

def toggle_inactive_left_style():
    return toggle_btn_style(active=False, left=True, dark=False)

def toggle_inactive_right_style():
    return toggle_btn_style(active=False, left=False, dark=False)
class LightThemeMixin:
    """Mixin to apply light theme styles to Qt widgets."""
    def apply_menu_style(self, widget):
        widget.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 172);
                border-radius: 24px;
                border: 1px solid rgba(31, 35, 40, 28);
            }
        """)

    def apply_close_btn_style(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #20242a;
                font: 16pt 'Segoe UI';
                border: none;
                border-radius: 12px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(31, 35, 40, 16);
                color: #111318;
            }
        """)

    def apply_gear_icon(self, label):
        # Use constants for sizing/colors
        gear_img = QImage(ICON_SIZE, ICON_SIZE, QImage.Format.Format_ARGB32)
        gear_img.fill(Qt.GlobalColor.transparent)
        painter = QPainter(gear_img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = ICON_SIZE / 2, ICON_SIZE / 2
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#232323"))
        painter.drawEllipse(QPointF(cx, cy), 10, 10)
        painter.setBrush(QColor("#e0e0e0"))
        painter.drawEllipse(QPointF(cx, cy), 4, 4)
        painter.end()
        label.setPixmap(QPixmap.fromImage(gear_img))
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label.raise_()

    def apply_author_label_style(self, label, widget):
        label.setStyleSheet(f"color: rgba(31, 35, 40, 160); font: {AUTHOR_FONT_SIZE}pt 'Segoe UI Variable'; background: transparent;")
        label.adjustSize()
        label.move(12, widget.height() - label.height() - 12)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label.raise_()

    def paintEvent(self, event, widget):
        painter = QPainter(widget)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(widget.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        radius = 24
        path.addRoundedRect(rect, radius, radius)
        bg = QLinearGradient(rect.topLeft(), rect.bottomRight())
        bg.setColorAt(0.0, QColor(255, 255, 255, 236))
        bg.setColorAt(0.55, QColor(245, 247, 250, 218))
        bg.setColorAt(1.0, QColor(232, 236, 242, 210))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawPath(path)
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
        painter.drawLine(24, 1, widget.width() - 24, 1)
        pen = QPen(QColor(20, 24, 32, 32), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        painter.end()

    def apply_theme(self):
        self.setStyleSheet("""
            QDialog {
                background: transparent;
                font-family: 'Segoe UI Variable', 'Segoe UI';
            }
            QLabel {
                color: #20242a;
                font: 600 12pt 'Segoe UI Variable';
            }
            QPushButton {
                background: rgba(255, 255, 255, 0.72);
                color: #20242a;
                border: 1px solid rgba(31, 35, 40, 0.10);
                border-radius: 16px;
                padding: 10px 16px;
                font: 700 12pt 'Segoe UI Variable';
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.94);
                border-color: rgba(31, 35, 40, 0.16);
            }
            QPushButton:pressed {
                background: rgba(232, 235, 240, 0.95);
            }
            QSlider {
                background: transparent;
                min-height: 40px;
            }
            QSlider::groove:horizontal {
                background: rgba(31, 35, 40, 0.10);
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 1px solid rgba(31, 35, 40, 0.16);
                width: 22px;
                height: 22px;
                margin: -8px 0;
                border-radius: 11px;
            }
            QComboBox {
                background: rgba(255, 255, 255, 0.72);
                color: #20242a;
                border: 1px solid rgba(31, 35, 40, 0.10);
                padding: 10px 14px;
                min-width: 120px;
                font: 650 12pt 'Segoe UI Variable';
                border-radius: 14px;
                outline: none;
            }
            QComboBox:hover {
                background: rgba(255, 255, 255, 0.94);
                border-color: rgba(31, 35, 40, 0.16);
            }
            QComboBox::drop-down {
                border: none;
                background: transparent;
                width: 32px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
                margin: 0px;
            }
            QComboBox QAbstractItemView {
                background: #ffffff;
                color: #20242a;
                selection-background-color: #eef1f5;
                selection-color: #20242a;
                border: 1px solid rgba(31, 35, 40, 0.10);
                border-radius: 12px;
                padding: 6px;
            }
        """)

    def tab_btn_style(self, selected=False):
        if selected:
            return """
                QPushButton {
                    background: rgba(255, 255, 255, 0.72);
                    color: #161a20;
                    border: 1px solid rgba(31, 35, 40, 0.08);
                    font: 700 11pt 'Segoe UI Variable';
                    border-radius: 16px;
                    text-align: left;
                    padding-left: 18px;
                }
            """
        else:
            return """
                QPushButton {
                    background: transparent;
                    color: rgba(31, 35, 40, 150);
                    border: none;
                    font: 600 11pt 'Segoe UI Variable';
                    border-radius: 16px;
                    text-align: left;
                    padding-left: 18px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.52);
                    color: #20242a;
                }
            """


    def get_color_dialog_stylesheet() -> str:
        """Return a stylesheet for QColorDialog that matches the light theme."""
        return """
            QWidget {
                background: #f5f5f5;
                color: #232323;
            }
            QColorDialog QWidget { background: #f5f5f5; }
            QPushButton { background: #ffffff; color: #232323; border: 1px solid #e0e0e0; }
            QPushButton:hover { background: #e0e0e0; }
            QSlider::groove:horizontal { background: #e0e0e0; }
            QComboBox, QSpinBox { background: #ffffff; color: #232323; }
        """
    def enable_blur_background(self, widget):
        # Ensure the dialog supports transparent regions so rounded corners clip the window
        try:
            widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            widget.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        except Exception:
            pass

    # Dynamic blur/eventFilter removed — no dynamic updates needed without blur

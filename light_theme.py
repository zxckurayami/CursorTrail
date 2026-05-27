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
                background: #f5f5f5;
                border-radius: 24px;
                border: 1px solid #e0e0e0;
            }
        """)

    def apply_close_btn_style(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #232323;
                font: bold 22pt 'Segoe UI';
                border: none;
            }
            QPushButton:hover { color: #ff5555; }
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
        label.setStyleSheet(f"color: #232323; font: {AUTHOR_FONT_SIZE}pt 'Segoe UI'; background: transparent;")
        label.adjustSize()
        label.move(12, widget.height() - label.height() - 12)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label.raise_()

    def paintEvent(self, event, widget):
        # Simple solid / translucent panel painting without blur
        painter = QPainter(widget)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = widget.rect()
        path = QPainterPath()
        radius = 24  # изменённый радиус закругления (в пикселях)
        path.addRoundedRect(QRectF(rect), radius, radius)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 255))
        painter.drawPath(path)
        pen = QPen(QColor(0, 0, 0, 30), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        painter.end()

    def apply_theme(self):
        # Use transparent background so rounded corners of the painted panel show
        self.setStyleSheet("""
            QDialog {
                background: transparent;
                border-radius: 12px;
            }
            QLabel {
                color: #232323;
                font: bold 16pt 'Segoe UI';
            }
            QPushButton {
                background: #f5f5f5;
                color: #232323;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 10px;
                font: bold 14pt 'Segoe UI';
            }
            QPushButton:hover {
                background: #e0e0e0;
                border-color: #bdbdbd;
            }
            QPushButton:pressed {
                background: #d6d6d6;
                border-color: #bdbdbd;
            }
            QSlider {
                background: transparent;
                min-height: 40px;
            }
            QSlider::groove:horizontal {
                background: #e0e0e0;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #232323;
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }
            QComboBox {
                background: #f5f5f5;
                color: #232323;
                border: 1px solid #e0e0e0;
                padding: 8px;
                min-width: 120px;
                font: bold 14pt 'Segoe UI';
                border-radius: 8px;
                outline: none;
            }
            QComboBox:hover {
                background: #e0e0e0;
                border-color: #bdbdbd;
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
                background: #f5f5f5;
                color: #232323;
                selection-background-color: #e0e0e0;
                selection-color: #232323;
                border-radius: 0px;
                padding: 4px;
            }
        """)

    def tab_btn_style(self, selected=False):
        if selected:
            return """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #fff, stop:0.12 #f5f5f5, stop:1 #e0e0e0);
                    color: #232323;
                    border: none;
                    font: bold 15pt 'Segoe UI';
                    border-radius: 0px;
                }
            """
        else:
            return """
                QPushButton {
                    background: transparent;
                    color: #888;
                    border: none;
                    font: 15pt 'Segoe UI';
                    border-radius: 0px;
                }
                QPushButton:hover {
                    background: #e0e0e0;
                    color: #232323;
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

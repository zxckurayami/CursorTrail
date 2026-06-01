"""Dark theme styles and utilities.

This module mirrors `light_theme.py` but with dark palette values.
"""

import sys
from PySide6.QtCore import Qt, QPointF, QRectF, QUrl, QEvent, QTimer
from PySide6.QtGui import QPixmap, QPainter, QImage, QColor, QLinearGradient, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect
try:
    # Qt 6 moved some blur/backends; QGraphicsBlurEffect is still in QtWidgets but platform-specific
    from PySide6.QtGui import QSurfaceFormat
except Exception:
    QSurfaceFormat = None

# Для системного блюра Windows
if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes

# Constants (match light_theme defaults)
ICON_SIZE = 36
AUTHOR_FONT_SIZE = 10

# Reuse the same toggle generator wrappers to maintain API
def toggle_active_style():
    return """
        QPushButton {
            background: #232323;
            color: #fff;
            border: 1px solid #2a2a2a;
            border-radius: 8px;
            font-weight: bold;
        }
    """

def toggle_inactive_style():
    return """
        QPushButton {
            background: #444;
            color: #888;
            border: 1px solid #2a2a2a;
            border-radius: 8px;
        }
    """

def toggle_btn_style(active: bool, left: bool) -> str:
    bg = "#232323" if active else "#444"
    fg = "#fff" if active else "#888"
    border = "#2a2a2a"
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

# Backwards-compatible wrappers for left/right using half-styles
def toggle_active_left_style():
    return toggle_btn_style(True, True)

def toggle_active_right_style():
    return toggle_btn_style(True, False)

def toggle_inactive_left_style():
    return toggle_btn_style(False, True)

def toggle_inactive_right_style():
    return toggle_btn_style(False, False)

class DarkThemeMixin:
    """Mixin for applying dark theme to PyQt6 widgets."""

    def apply_menu_style(self, widget):
        widget.setStyleSheet("""
            QWidget {
                background: rgba(18, 19, 22, 188);
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 24);
            }
        """)

    def apply_close_btn_style(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #fff;
                font: 16pt 'Segoe UI';
                border: none;
                border-radius: 12px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 18);
                color: #fff;
            }
        """)

    def apply_gear_icon(self, label):
        gear_img = QImage(ICON_SIZE, ICON_SIZE, QImage.Format.Format_ARGB32)
        gear_img.fill(Qt.GlobalColor.transparent)
        painter = QPainter(gear_img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = ICON_SIZE / 2, ICON_SIZE / 2
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#fff"))
        painter.drawEllipse(QPointF(cx, cy), 10, 10)
        painter.setBrush(QColor("#181818"))
        painter.drawEllipse(QPointF(cx, cy), 4, 4)
        painter.end()
        label.setPixmap(QPixmap.fromImage(gear_img))
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label.raise_()

    def apply_author_label_style(self, label, widget):
        label.setStyleSheet(f"color: rgba(255, 255, 255, 150); font: {AUTHOR_FONT_SIZE}pt 'Segoe UI Variable'; background: transparent;")
        label.adjustSize()
        label.move(12, widget.height() - label.height() - 12)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label.raise_()

    def enable_windows_blur(self):
        """Enable Acrylic blur on Windows 10+."""
        if sys.platform != "win32":
            return
        hwnd = self.winId().__int__()
        class ACCENTPOLICY(ctypes.Structure):
            _fields_ = [("nAccentState", ctypes.c_int),
                        ("nFlags", ctypes.c_int),
                        ("nColor", ctypes.c_uint),
                        ("nAnimationId", ctypes.c_int)]
        class WINCOMPATTRDATA(ctypes.Structure):
            _fields_ = [("nAttribute", ctypes.c_int),
                        ("pData", ctypes.c_void_p),
                        ("ulDataSize", ctypes.c_size_t)]
        accent = ACCENTPOLICY()
        accent.nAccentState = 4  # ACCENT_ENABLE_ACRYLICBLURBEHIND
        accent.nFlags = 2
        accent.nColor = 0x99000000  # ARGB
        data = WINCOMPATTRDATA()
        data.nAttribute = 19  # WCA_ACCENT_POLICY
        data.pData = ctypes.byref(accent)
        data.ulDataSize = ctypes.sizeof(accent)
        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))

    def paintEvent(self, event, widget):
        painter = QPainter(widget)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(widget.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = 24
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        bg = QLinearGradient(rect.topLeft(), rect.bottomRight())
        bg.setColorAt(0.0, QColor(28, 29, 33, 236))
        bg.setColorAt(0.45, QColor(14, 15, 18, 226))
        bg.setColorAt(1.0, QColor(8, 9, 11, 220))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawPath(path)
        painter.setPen(QPen(QColor(255, 255, 255, 28), 1))
        painter.drawLine(24, 1, widget.width() - 24, 1)
        pen = QPen(QColor(255, 255, 255, 22), 1)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
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
                color: #f6f7f9;
                font: 600 12pt 'Segoe UI Variable';
            }
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                color: #f6f7f9;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 16px;
                padding: 10px 16px;
                font: 700 12pt 'Segoe UI Variable';
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.13);
                border-color: rgba(255, 255, 255, 0.18);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.07);
            }
            QSlider {
                background: transparent;
                min-height: 40px;
            }
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.10);
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #f6f7f9;
                border: 1px solid rgba(255, 255, 255, 0.25);
                width: 22px;
                height: 22px;
                margin: -8px 0;
                border-radius: 11px;
            }
            QComboBox {
                background: rgba(255, 255, 255, 0.08);
                color: #f6f7f9;
                border: 1px solid rgba(255, 255, 255, 0.10);
                padding: 10px 14px;
                min-width: 120px;
                font: 650 12pt 'Segoe UI Variable';
                border-radius: 14px;
                outline: none;
            }
            QComboBox:hover {
                background: rgba(255, 255, 255, 0.13);
                border-color: rgba(255, 255, 255, 0.18);
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
                background: #18191d;
                color: #f6f7f9;
                selection-background-color: rgba(255, 255, 255, 0.10);
                selection-color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                padding: 6px;
            }
        """)

    def tab_btn_style(self, selected=False):
        if selected:
            return """
                QPushButton {
                    background: rgba(255, 255, 255, 0.10);
                    color: #fff;
                    border: 1px solid rgba(255, 255, 255, 0.12);
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
                    color: rgba(255, 255, 255, 165);
                    border: none;
                    font: 600 11pt 'Segoe UI Variable';
                    border-radius: 16px;
                    text-align: left;
                    padding-left: 18px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.08);
                    color: #fff;
                }
            """


    def get_color_dialog_stylesheet() -> str:
        """Return a stylesheet for QColorDialog that matches the dark theme."""
        return """
            QWidget {
                background: #141414;
                color: #fff;
            }
            QColorDialog QWidget { background: #141414; }
            QPushButton { background: #2b2b2b; color: #fff; border: 1px solid #232323; }
            QPushButton:hover { background: #333; }
            QSlider::groove:horizontal { background: #232323; }
            QComboBox, QSpinBox { background: #232323; color: #fff; }
        """
    def enable_blur_background(self, widget):
        # Ensure the dialog supports transparent regions so rounded corners clip the window
        try:
            widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            widget.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        except Exception:
            pass

    def eventFilter(self, watched, event):
        try:
            if event.type() in (QEvent.Move, QEvent.Resize, QEvent.Show):
                try:
                    watched.update()
                except Exception:
                    pass
            elif event.type() == QEvent.Hide:
                try:
                    if hasattr(self, '_dynamic_blur_timer'):
                        self._dynamic_blur_timer.stop()
                except Exception:
                    pass
        except Exception:
            pass
        return False

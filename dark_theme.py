# --- Стили для переключателей (ToggleSwitch) в тёмной теме ---
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

# Персонализованные стили для левой/правой кнопок переключателя (тёмная тема)
def toggle_active_left_style():
    return """
        QPushButton {
            background: #232323;
            color: #fff;
            border: 1px solid #2a2a2a;
            border-top-left-radius: 8px;
            border-bottom-left-radius: 8px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
            font-weight: bold;
        }
    """

def toggle_active_right_style():
    return """
        QPushButton {
            background: #232323;
            color: #fff;
            border: 1px solid #2a2a2a;
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
            font-weight: bold;
        }
    """

def toggle_inactive_left_style():
    return """
        QPushButton {
            background: #444;
            color: #888;
            border: 1px solid #2a2a2a;
            border-top-left-radius: 8px;
            border-bottom-left-radius: 8px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
        }
    """

def toggle_inactive_right_style():
    return """
        QPushButton {
            background: #444;
            color: #888;
            border: 1px solid #2a2a2a;
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
        }
    """
# dark_theme.py
# UI компоненты и стили для тёмной темы
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class DarkThemeMixin:
    def apply_menu_style(self, widget):
        widget.setStyleSheet("""
            QWidget {
                background: #141414;
                border-radius: 12px;
                border: 1px solid #232323;
            }
        """)

    def apply_close_btn_style(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #fff;
                font: bold 22pt 'Segoe UI';
                border: none;
            }
            QPushButton:hover { color: #ff5555; }
        """)

    def apply_gear_icon(self, label):
        from PyQt5.QtGui import QPixmap, QPainter, QImage, QColor
        from PyQt5.QtCore import QPointF
        gear_img = QImage(36, 36, QImage.Format_ARGB32)
        gear_img.fill(Qt.transparent)
        painter = QPainter(gear_img)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy = 18, 18
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#fff"))
        painter.drawEllipse(QPointF(cx, cy), 10, 10)
        painter.setBrush(QColor("#181818"))
        painter.drawEllipse(QPointF(cx, cy), 4, 4)
        painter.end()
        label.setPixmap(QPixmap.fromImage(gear_img))
        label.setAttribute(Qt.WA_TransparentForMouseEvents)
        label.raise_()

    def apply_author_label_style(self, label, widget):
        label.setStyleSheet("color: #fff; font: 10pt 'Segoe UI'; background: transparent;")
        label.adjustSize()
        label.move(12, widget.height() - label.height() - 12)
        label.setAttribute(Qt.WA_TransparentForMouseEvents)
        label.raise_()

    def paintEvent(self, event, widget):
        painter = QPainter(widget)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = widget.rect()
        from PyQt5.QtGui import QLinearGradient, QPainterPath, QColor, QPen
        from PyQt5.QtCore import QRectF
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0, QColor("#141414"))
        grad.setColorAt(0.5, QColor("#181818"))
        grad.setColorAt(1, QColor("#141414"))
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect.adjusted(1,1,-1,-1)), 12, 12)
        painter.setPen(Qt.NoPen)
        painter.setBrush(grad)
        painter.drawPath(path)
        pen = QPen(QColor("#232323"), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
    def apply_theme(self):
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #181818,
                    stop:0.5 #232323,
                    stop:1 #181818);
                border-radius: 12px;
            }
            QLabel {
                color: #fff;
                font: bold 16pt 'Segoe UI';
            }
            QPushButton {
                background: #232323;
                color: #fff;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                padding: 10px;
                font: bold 14pt 'Segoe UI';
            }
            QPushButton:hover {
                background: #2a2a2a;
                border-color: #333;
            }
            QPushButton:pressed {
                background: #1e1e1e;
                border-color: #333;
            }
            QSlider {
                background: transparent;
                min-height: 40px;
            }
            QSlider::groove:horizontal {
                background: #232323;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #fff;
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }
            QComboBox {
                background: #232323;
                color: #fff;
                border: 1px solid #2a2a2a;
                padding: 8px;
                min-width: 120px;
                font: bold 14pt 'Segoe UI';
                border-radius: 8px;
                outline: none;
            }
            QComboBox:hover {
                background: #2a2a2a;
                border-color: #333;
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
                background: #232323;
                color: #fff;
                selection-background-color: #444;
                selection-color: #fff;
                border-radius: 8px;
                padding: 4px;
            }
        """)

    def tab_btn_style(self, selected=False):
        if selected:
            return """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #232323, stop:0.12 #232323, stop:1 #181818);
                    color: #fff;
                    border: none;
                    font: bold 15pt 'Segoe UI';
                    border-radius: 0px;
                }
            """
        else:
            return """
                QPushButton {
                    background: transparent;
                    color: #bbb;
                    border: none;
                    font: 15pt 'Segoe UI';
                    border-radius: 0px;
                }
                QPushButton:hover {
                    background: #232323;
                    color: #fff;
                }
            """

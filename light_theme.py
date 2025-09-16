# --- Стили для переключателей (ToggleSwitch) в светлой теме ---
def toggle_active_style():
    return """
        QPushButton {
            background: #fff;
            color: #232323;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            font-weight: bold;
        }
    """

def toggle_inactive_style():
    return """
        QPushButton {
            background: #e0e0e0;
            color: #888;
            border: 1px solid #d6d6d6;
            border-radius: 8px;
        }
    """

# Персонализованные стили для левой/правой кнопок переключателя
def toggle_active_left_style():
    return """
        QPushButton {
            background: #fff;
            color: #232323;
            border: 1px solid #e0e0e0;
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
            background: #fff;
            color: #232323;
            border: 1px solid #e0e0e0;
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
            background: #e0e0e0;
            color: #888;
            border: 1px solid #d6d6d6;
            border-top-left-radius: 8px;
            border-bottom-left-radius: 8px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
        }
    """

def toggle_inactive_right_style():
    return """
        QPushButton {
            background: #e0e0e0;
            color: #888;
            border: 1px solid #d6d6d6;
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
        }
    """
# light_theme.py
# UI компоненты и стили для светлой темы
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class LightThemeMixin:
    def apply_menu_style(self, widget):
        widget.setStyleSheet("""
            QWidget {
                background: #f5f5f5;
                border-radius: 12px;
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
        from PyQt5.QtGui import QPixmap, QPainter, QImage, QColor
        from PyQt5.QtCore import QPointF
        gear_img = QImage(36, 36, QImage.Format_ARGB32)
        gear_img.fill(Qt.transparent)
        painter = QPainter(gear_img)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy = 18, 18
        painter.setPen(QColor("#232323"))
        painter.setBrush(QColor("#232323"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), 10, 10)
        painter.setBrush(QColor("#e0e0e0"))
        painter.drawEllipse(QPointF(cx, cy), 4, 4)
        painter.end()
        label.setPixmap(QPixmap.fromImage(gear_img))
        label.setAttribute(Qt.WA_TransparentForMouseEvents)
        label.raise_()

    def apply_author_label_style(self, label, widget):
        label.setStyleSheet("color: #232323; font: 10pt 'Segoe UI'; background: transparent;")
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
        grad.setColorAt(0, QColor("#f5f5f5"))
        grad.setColorAt(0.5, QColor("#ffffff"))
        grad.setColorAt(1, QColor("#e0e0e0"))
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect.adjusted(1,1,-1,-1)), 12, 12)
        painter.setPen(Qt.NoPen)
        painter.setBrush(grad)
        painter.drawPath(path)
        pen = QPen(QColor("#bdbdbd"), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
    def apply_theme(self):
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f5f5f5,
                    stop:0.5 #ffffff,
                    stop:1 #e0e0e0);
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
                border-radius: 8px;
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
                border-radius: 8px;
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

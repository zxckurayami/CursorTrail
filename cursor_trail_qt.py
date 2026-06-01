import sys, os, json, random, math, colorsys, subprocess
import logging
from PySide6.QtWidgets import (
    QApplication, QWidget, QStackedWidget, QSlider, QColorDialog, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QDialog, QCheckBox, QFrame, QGridLayout, QSystemTrayIcon, QMenu, QStyle, QListWidget, QListWidgetItem, QAbstractItemView, QScrollArea, QComboBox, QSizePolicy, QLineEdit
)
from PySide6.QtCore import Qt, QTimer, QPoint, QRect, QPointF, QSize, QRectF, QPropertyAnimation, QEasingCurve, QLibraryInfo, QTranslator, Signal, Property, Slot
from PySide6.QtGui import QPainter, QColor, QPen, QCursor, QIcon, QFont, QLinearGradient, QImage, QPainterPath, QPalette, QPixmap, QIntValidator
from collections import deque


_qt_color_dialog_translator = None


def _resolve_dark_theme(parent, fallback=False):
    current = parent
    while current is not None:
        if hasattr(current, "dark_theme_enabled"):
            return bool(getattr(current, "dark_theme_enabled"))
        current = current.parent() if hasattr(current, "parent") else None
    return bool(fallback)


def _resolve_language(parent, fallback="ru"):
    current = parent
    while current is not None:
        if hasattr(current, "current_language"):
            return getattr(current, "current_language") or fallback
        current = current.parent() if hasattr(current, "parent") else None
    return fallback


def _color_dialog_title(parent):
    language = _resolve_language(parent)
    return {
        "ru": "Выбор цвета",
        "en": "Select color",
        "zh": "选择颜色",
        "ja": "色を選択",
    }.get(language, "Select color")


def _install_color_dialog_translation(parent):
    global _qt_color_dialog_translator

    language = _resolve_language(parent)
    qt_language = {
        "ru": "ru",
        "zh": "zh_CN",
        "ja": "ja",
    }.get(language)

    app = QApplication.instance()
    if app is None:
        return

    if _qt_color_dialog_translator is not None:
        app.removeTranslator(_qt_color_dialog_translator)
        _qt_color_dialog_translator = None

    if qt_language is None:
        return

    translator = QTranslator(app)
    translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if translator.load(f"qtbase_{qt_language}", translations_path):
        app.installTranslator(translator)
        _qt_color_dialog_translator = translator


def _color_dialog_stylesheet(dark=False):
    if dark:
        return """
            QColorDialog, QColorDialog QWidget {
                background: #101010;
                color: #ffffff;
                font: 10pt 'Segoe UI';
            }
            QColorDialog QLabel {
                color: #ffffff;
                background: transparent;
                border: none;
                font: bold 10pt 'Segoe UI';
            }
            QColorDialog QPushButton {
                background: #232323;
                color: #ffffff;
                border: 1px solid #2f2f2f;
                border-radius: 8px;
                padding: 7px 12px;
                font: bold 10pt 'Segoe UI';
                min-height: 20px;
            }
            QColorDialog QPushButton:hover {
                background: #2b2b2b;
                border-color: #3a3a3a;
            }
            QColorDialog QPushButton:pressed {
                background: #1d1d1d;
            }
            QColorDialog QLineEdit,
            QColorDialog QSpinBox,
            QColorDialog QAbstractSpinBox {
                background: #181818;
                color: #ffffff;
                border: 1px solid #2f2f2f;
                border-radius: 6px;
                padding: 4px 8px;
                selection-background-color: #ffffff;
                selection-color: #101010;
            }
            QColorDialog QSpinBox::up-button,
            QColorDialog QSpinBox::down-button {
                background: #232323;
                border: none;
                width: 16px;
            }
            QColorDialog QFrame {
                background: transparent;
                border: none;
            }
            QColorDialog QSlider::groove:horizontal {
                background: #232323;
                height: 8px;
                border-radius: 4px;
            }
            QColorDialog QSlider::handle:horizontal {
                background: #ffffff;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """

    return """
        QColorDialog, QColorDialog QWidget {
            background: #f5f5f5;
            color: #232323;
            font: 10pt 'Segoe UI';
        }
        QColorDialog QLabel {
            color: #232323;
            background: transparent;
            border: none;
            font: bold 10pt 'Segoe UI';
        }
        QColorDialog QPushButton {
            background: #ffffff;
            color: #232323;
            border: 1px solid #d8d8d8;
            border-radius: 8px;
            padding: 7px 12px;
            font: bold 10pt 'Segoe UI';
            min-height: 20px;
        }
        QColorDialog QPushButton:hover {
            background: #eeeeee;
            border-color: #c8c8c8;
        }
        QColorDialog QPushButton:pressed {
            background: #e2e2e2;
        }
        QColorDialog QLineEdit,
        QColorDialog QSpinBox,
        QColorDialog QAbstractSpinBox {
            background: #ffffff;
            color: #232323;
            border: 1px solid #d8d8d8;
            border-radius: 6px;
            padding: 4px 8px;
            selection-background-color: #232323;
            selection-color: #ffffff;
        }
        QColorDialog QSpinBox::up-button,
        QColorDialog QSpinBox::down-button {
            background: #f5f5f5;
            border: none;
            width: 16px;
        }
        QColorDialog QFrame {
            background: transparent;
            border: none;
        }
        QColorDialog QSlider::groove:horizontal {
            background: #e0e0e0;
            height: 8px;
            border-radius: 4px;
        }
        QColorDialog QSlider::handle:horizontal {
            background: #232323;
            width: 18px;
            height: 18px;
            margin: -5px 0;
            border-radius: 9px;
        }
    """


def _apply_color_dialog_theme(dlg, dark=False):
    surface = QColor("#101010" if dark else "#f5f5f5")
    text = QColor("#ffffff" if dark else "#232323")
    field = QColor("#181818" if dark else "#ffffff")
    palette = dlg.palette()
    palette.setColor(QPalette.ColorRole.Window, surface)
    palette.setColor(QPalette.ColorRole.Base, field)
    palette.setColor(QPalette.ColorRole.AlternateBase, field)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Button, field)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#ffffff" if dark else "#232323"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#101010" if dark else "#ffffff"))
    dlg.setPalette(palette)
    dlg.setStyleSheet(_color_dialog_stylesheet(dark))


def _make_close_icon(dark=False):
    pix = QPixmap(24, 24)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(QColor("#ffffff" if dark else "#20242a"), 2.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawLine(QPointF(5.5, 5.5), QPointF(18.5, 18.5))
    painter.drawLine(QPointF(18.5, 5.5), QPointF(5.5, 18.5))
    painter.end()
    return QIcon(pix)


def _center_dialog_on_owner(dialog, owner=None):
    app = QApplication.instance()
    center = None
    source = owner or dialog.parentWidget()

    if source is not None:
        try:
            source_window = source.window()
            if source_window is not None and source_window is not dialog:
                center = source_window.mapToGlobal(source_window.rect().center())
            else:
                center = source.mapToGlobal(source.rect().center())
        except Exception:
            try:
                center = source.frameGeometry().center()
            except Exception:
                center = None

    if center is None and app is not None:
        active = app.activeWindow()
        if active is not None and active is not dialog:
            center = active.frameGeometry().center()

    screen = QApplication.screenAt(center) if center is not None else None
    if screen is None and app is not None:
        screen = app.primaryScreen()

    if center is None and screen is not None:
        center = screen.availableGeometry().center()
    if center is None:
        return

    pos = center - dialog.rect().center()
    if screen is not None:
        available = screen.availableGeometry()
        x = max(available.left(), min(pos.x(), available.right() - dialog.width() + 1))
        y = max(available.top(), min(pos.y(), available.bottom() - dialog.height() + 1))
        pos = QPoint(x, y)
    dialog.move(pos)


def themed_get_color(initial, parent=None, dark=False):
    use_dark = _resolve_dark_theme(parent, dark)
    dlg = ModernColorDialog(initial if isinstance(initial, QColor) else QColor(initial), parent, use_dark)
    if dlg.exec():
        return dlg.selected_color()
    return QColor()

if sys.platform == "win32":
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0

# Configure simple logging for the application
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')

def hex_to_qcolor(hex_color):
    hex_color = hex_color.lstrip('#')
    return QColor(int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))

def get_settings_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), 'settings.json')
    else:
        return os.path.join(os.path.dirname(__file__), 'settings.json')

class ToggleSwitch(QWidget):
    """Compact macOS-style switch with the same public API as the old two-button control."""
    valueChanged = Signal(bool)

    def set_dark_theme(self, enabled):
        self.dark_theme_enabled = bool(enabled)
        self.update()

    def __init__(self, value=True, parent=None):
        super().__init__(parent)
        self.dark_theme_enabled = _resolve_dark_theme(parent, False)
        self.setFixedSize(58, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._value = bool(value)

    def setValue(self, value):
        self.value = bool(value)
        self.set_dark_theme(_resolve_dark_theme(self.parent(), self.dark_theme_enabled))
        self.update()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        prev = getattr(self, '_value', None)
        self._value = val
        # Emit signal when value actually changes
        try:
            if prev is None or prev != val:
                self.valueChanged.emit(bool(val))
        except Exception:
            logger.debug('Failed to emit valueChanged signal', exc_info=True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setValue(not self.value)
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        dark = getattr(self, "dark_theme_enabled", False)
        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        radius = rect.height() / 2

        if self.value:
            track = QColor("#e9edf2" if dark else "#202327")
            border = QColor("#ffffff" if dark else "#202327")
            knob = QColor("#111318" if dark else "#ffffff")
            shadow = QColor(0, 0, 0, 90 if dark else 40)
        else:
            track = QColor("#24262a" if dark else "#eef0f3")
            border = QColor("#32353a" if dark else "#d9dde3")
            knob = QColor("#8c929b" if dark else "#9aa1ab")
            shadow = QColor(0, 0, 0, 70 if dark else 25)

        painter.setPen(QPen(border, 1))
        painter.setBrush(track)
        painter.drawRoundedRect(rect, radius, radius)

        knob_size = 22
        knob_x = self.width() - knob_size - 5 if self.value else 5
        knob_rect = QRectF(knob_x, (self.height() - knob_size) / 2, knob_size, knob_size)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(shadow)
        painter.drawEllipse(knob_rect.translated(0, 1.5))
        painter.setBrush(knob)
        painter.drawEllipse(knob_rect)

class ColorSliderWidget(QWidget):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.dark_theme_enabled = _resolve_dark_theme(parent, False)
        self.setMinimumHeight(48)
        self.setMouseTracking(True)
        self.colors = list(colors)
        self.selected = 0
        self.dragging = False
        self.drag_index = None
        self.drag_offset = 0
        self.rects = []
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_colors(self, colors):
        self.colors = list(colors)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margin = 4
        btn_w, btn_h = 48, 36
        spacing = 8
        x = margin
        self.rects = []
        for i, color in enumerate(self.colors):
            rect = QRect(x, (self.height()-btn_h)//2, btn_w, btn_h)
            self.rects.append(rect)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(rect, 8, 8)
            # Обводка
            if i == self.selected:
                painter.setPen(QColor("#ffffff" if getattr(self, "dark_theme_enabled", False) else "#202327"))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(rect.adjusted(-2,-2,2,2), 10, 10)
            x += btn_w + spacing
        self.setMinimumWidth(x+margin)

    def mousePressEvent(self, event):
        for i, rect in enumerate(self.rects):
            p = event.position().toPoint()
            if rect.contains(p):
                self.selected = i
                self.dragging = True
                self.drag_index = i
                self.drag_offset = p.x() - rect.x()
                self.update()
                break

    def mouseMoveEvent(self, event):
        if self.dragging and self.drag_index is not None:
            x = event.position().toPoint().x() - self.drag_offset
            # Определяем новую позицию
            new_index = self.drag_index
            for i, rect in enumerate(self.rects):
                if i != self.drag_index and rect.contains(QPoint(int(x+24), int(rect.center().y()))):
                    new_index = i
                    break
            if new_index != self.drag_index:
                color = self.colors.pop(self.drag_index)
                self.colors.insert(new_index, color)
                self.drag_index = new_index
                self.selected = new_index
                self.update()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.drag_index = None
        self.update()
        # Сигнал о смене порядка
        if hasattr(self, 'onOrderChanged'):
            self.onOrderChanged(self.colors)
        # Открыть QColorDialog по клику
        for i, rect in enumerate(self.rects):
            p = event.position().toPoint()
            if rect.contains(p):
                color = themed_get_color(QColor(self.colors[i]), self, getattr(self, 'dark_theme_enabled', False))
                if color.isValid():
                    self.colors[i] = color.name()
                    self.selected = i
                    self.update()
                    if hasattr(self, 'onOrderChanged'):
                        self.onOrderChanged(self.colors)
                break

    def sizeHint(self):
        return QSize(max(200, len(self.colors)*56), 48)

    def get_colors(self):
        return self.colors

class GradientSliderWidget(QWidget):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.dark_theme_enabled = _resolve_dark_theme(parent, False)
        self.setMinimumHeight(48)
        self.setMouseTracking(True)
        self.colors = list(colors)
        self.selected = 0
        self.dragging = False
        self.drag_index = None
        self.drag_offset = 0
        self.knob_radius = 16
        self.knob_border = 3
        self.knob_rects = []
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_colors(self, colors):
        self.colors = list(colors)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margin = self.knob_radius + 6
        bar_y = self.height() // 2
        bar_h = 10
        bar_rect = QRect(margin, bar_y - bar_h // 2, self.width() - 2 * margin, bar_h)
        # Градиентная линия
        grad = QLinearGradient(bar_rect.left(), bar_rect.center().y(), bar_rect.right(), bar_rect.center().y())
        for i, color in enumerate(self.colors):
            grad.setColorAt(i / (len(self.colors) - 1), QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawRoundedRect(bar_rect, bar_h // 2, bar_h // 2)
        # Квадратные маркеры меньшего размера, без обводки
        self.knob_rects = []
        knob_size = 25  # уменьшенный размер
        for i, color in enumerate(self.colors):
            x = bar_rect.left() + i * bar_rect.width() // (len(self.colors) - 1)
            knob_rect = QRect(x - knob_size // 2, bar_y - knob_size // 2, knob_size, knob_size)
            self.knob_rects.append(knob_rect)
            # Маленький градиент внутри маркера для глубины
            kgrad = QLinearGradient(QPointF(knob_rect.topLeft()), QPointF(knob_rect.bottomRight()))
            base_col = QColor(color)
            kgrad.setColorAt(0, base_col.lighter(115))
            kgrad.setColorAt(1, base_col.darker(115))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(kgrad)
            painter.drawRoundedRect(knob_rect, 6, 6)
            # Тонкая обводка
            border_color = QColor("#ffffff" if getattr(self, "dark_theme_enabled", False) else "#202327")
            pen = QPen(border_color)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(knob_rect.adjusted(0,0,0,0), 6, 6)
            # Выделение (закруглённая обводка вокруг маркера)
            if i == self.selected:
                sel_rect = knob_rect.adjusted(-3, -3, 3, 3)
                painter.setPen(QPen(border_color, 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(sel_rect, 8, 8)

    def mousePressEvent(self, event):
        for i, rect in enumerate(self.knob_rects):
            p = event.position().toPoint()
            if rect.contains(p):
                self.selected = i
                self.dragging = True
                self.drag_index = i
                self.drag_offset = p.x() - rect.center().x()
                self.update()
                break

    def mouseMoveEvent(self, event):
        if self.dragging and self.drag_index is not None:
            x = event.position().toPoint().x() - self.drag_offset
            margin = self.knob_radius + 6
            bar_left = margin
            bar_right = self.width() - margin
            x = max(bar_left, min(bar_right, x))
            # Определяем новую позицию
            rel = (x - bar_left) / (bar_right - bar_left)
            new_index = round(rel * (len(self.colors) - 1))
            if new_index != self.drag_index:
                color = self.colors.pop(self.drag_index)
                self.colors.insert(new_index, color)
                self.drag_index = new_index
                self.selected = new_index
                self.update()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.drag_index = None
        self.update()
        # Сигнал о смене порядка
        if hasattr(self, 'onOrderChanged'):
            self.onOrderChanged(self.colors)
        # Открыть QColorDialog по клику
        for i, rect in enumerate(self.knob_rects):
            p = event.position().toPoint()
            if rect.contains(p):
                color = themed_get_color(QColor(self.colors[i]), self, getattr(self, 'dark_theme_enabled', False))
                if color.isValid():
                    self.colors[i] = color.name()
                    self.selected = i
                    self.update()
                    if hasattr(self, 'onOrderChanged'):
                        self.onOrderChanged(self.colors)
                break

    def sizeHint(self):
        return QSize(max(220, len(self.colors)*40), 48)

    def get_colors(self):
        return self.colors

class ColorGradientPicker(QWidget):
    colorsChanged = Signal(list)

    def set_dark_theme(self, enabled):
        self.dark_theme_enabled = bool(enabled)
        self.slider.dark_theme_enabled = bool(enabled)
        if enabled:
            btn_style = """
                QPushButton {
                    background: rgba(255, 255, 255, 0.08);
                    color: #fff;
                    font: bold 13pt 'Segoe UI Variable';
                    border: 1px solid rgba(255, 255, 255, 0.10);
                    border-radius: 12px;
                    padding: 0px;
                    text-align: center;
                }
                QPushButton:hover { background: rgba(255, 255, 255, 0.13); }
            """
        else:
            btn_style = """
                QPushButton {
                    background: rgba(255, 255, 255, 0.72);
                    color: #232323;
                    font: bold 13pt 'Segoe UI Variable';
                    border-radius: 12px;
                    border: 1px solid rgba(25, 28, 34, 0.10);
                    padding: 0px;
                    text-align: center;
                }
                QPushButton:hover { background: rgba(255, 255, 255, 0.92); }
                QPushButton:pressed { background: rgba(238, 240, 244, 0.95); }
            """
        self.minus_btn.setStyleSheet(btn_style)
        self.plus_btn.setStyleSheet(btn_style)
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.dark_theme_enabled = False
        self.colors = list(colors) if colors else ["#3399ff", "#ffffff"]
        self.setMinimumHeight(56)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.minus_btn = QPushButton("−")
        self.minus_btn.setFixedSize(36, 36)
        self.minus_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                color: #232323;
                font: bold 13pt 'Segoe UI Variable';
                border-radius: 8px;
                border: 0px solid #bdbdbd;
                padding: 0px;
                text-align: center;
            }
            QPushButton:hover { background: #e0e0e0; }
            QPushButton:pressed { background: #d6d6d6; }
        """)
        self.minus_btn.clicked.connect(self.remove_color)
        layout.addWidget(self.minus_btn)
        self.slider = GradientSliderWidget(self.colors)
        self.slider.dark_theme_enabled = self.dark_theme_enabled
        self.slider.onOrderChanged = self.on_colors_changed
        layout.addWidget(self.slider, 1)
        self.plus_btn = QPushButton("+")
        self.plus_btn.setFixedSize(36, 36)
        self.plus_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                color: #232323;
                font: bold 13pt 'Segoe UI Variable';
                border-radius: 8px;
                border: 0px solid #bdbdbd;
                padding: 0px;
                text-align: center;
            }
            QPushButton:hover { background: #e0e0e0; }
            QPushButton:pressed { background: #d6d6d6; }
        """)
        self.plus_btn.clicked.connect(self.add_color)
        layout.addWidget(self.plus_btn)
        layout.addStretch()

    def on_colors_changed(self, colors):
        self.colors = list(colors)
        self.slider.set_colors(self.colors)
        self.colorsChanged.emit(list(self.colors))

    def add_color(self):
        color = themed_get_color(QColor("#ffffff"), self, getattr(self, 'dark_theme_enabled', False))
        if color.isValid():
            insert_pos = self.slider.selected + 1
            self.colors.insert(insert_pos, color.name())
            self.slider.selected = insert_pos
            self.slider.set_colors(self.colors)
            self.slider.update()
            self.colorsChanged.emit(list(self.colors))

    def remove_color(self):
        if len(self.colors) > 2:
            idx = self.slider.selected
            self.colors.pop(idx)
            self.slider.selected = max(0, idx-1)
            self.slider.set_colors(self.colors)
            self.slider.update()
            self.colorsChanged.emit(list(self.colors))

    def get_colors(self):
        return self.slider.get_colors()

    def set_colors(self, colors):
        try:
            self.colors = list(colors)
            self.slider.set_colors(self.colors)
            self.slider.update()
            self.colorsChanged.emit(list(self.colors))
        except Exception:
            logger.exception('Failed to set colors for ColorGradientPicker')


class ColorPlaneWidget(QWidget):
    colorChanged = Signal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hue = 0.0
        self.saturation = 1.0
        self.value = 1.0
        self.setFixedSize(320, 300)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)

    def set_hsv(self, hue, saturation=None, value=None):
        self.hue = max(0.0, min(1.0, float(hue)))
        if saturation is not None:
            self.saturation = max(0.0, min(1.0, float(saturation)))
        if value is not None:
            self.value = max(0.0, min(1.0, float(value)))
        self.update()

    def _color_at(self, pos):
        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        x = max(rect.left(), min(rect.right(), pos.x()))
        y = max(rect.top(), min(rect.bottom(), pos.y()))
        saturation = (x - rect.left()) / max(1.0, rect.width())
        value = 1.0 - ((y - rect.top()) / max(1.0, rect.height()))
        r, g, b = colorsys.hsv_to_rgb(self.hue, saturation, value)
        self.saturation = saturation
        self.value = value
        return QColor(int(r * 255), int(g * 255), int(b * 255))

    def _pick(self, pos):
        color = self._color_at(pos)
        self.colorChanged.emit(color)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pick(event.position())
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._pick(event.position())
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        path = QPainterPath()
        path.addRoundedRect(rect, 18, 18)
        painter.setClipPath(path)

        r, g, b = colorsys.hsv_to_rgb(self.hue, 1.0, 1.0)
        hue_color = QColor(int(r * 255), int(g * 255), int(b * 255))
        sat_gradient = QLinearGradient(rect.topLeft(), rect.topRight())
        sat_gradient.setColorAt(0.0, QColor("#ffffff"))
        sat_gradient.setColorAt(1.0, hue_color)
        painter.fillRect(rect, sat_gradient)

        value_gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        value_gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
        value_gradient.setColorAt(1.0, QColor(0, 0, 0, 255))
        painter.fillRect(rect, value_gradient)
        painter.setClipping(False)

        handle = QPointF(rect.left() + rect.width() * self.saturation, rect.top() + rect.height() * (1.0 - self.value))
        painter.setPen(QPen(QColor(0, 0, 0, 150), 4))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(handle, 8, 8)
        painter.setPen(QPen(QColor(255, 255, 255, 235), 2))
        painter.drawEllipse(handle, 7, 7)


class HueSliderWidget(QWidget):
    hueChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hue = 0.0
        self.setFixedSize(28, 300)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_hue(self, hue):
        self.hue = max(0.0, min(1.0, float(hue)))
        self.update()

    def _pick(self, pos):
        rect = QRectF(5, 1, self.width() - 10, self.height() - 2)
        y = max(rect.top(), min(rect.bottom(), pos.y()))
        self.hue = (y - rect.top()) / max(1.0, rect.height())
        self.hueChanged.emit(self.hue)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pick(event.position())
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._pick(event.position())
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(5, 1, self.width() - 10, self.height() - 2)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        for i, hue in enumerate((0.0, 1 / 6, 2 / 6, 3 / 6, 4 / 6, 5 / 6, 1.0)):
            r, g, b = colorsys.hsv_to_rgb(hue % 1.0, 1.0, 1.0)
            gradient.setColorAt(i / 6, QColor(int(r * 255), int(g * 255), int(b * 255)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawRoundedRect(rect, 7, 7)

        y = rect.top() + rect.height() * self.hue
        painter.setPen(QPen(QColor(0, 0, 0, 130), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(2, y), QPointF(self.width() - 2, y))
        painter.setPen(QPen(QColor(255, 255, 255, 235), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(4, y), QPointF(self.width() - 4, y))


class ModernColorDialog(QDialog):
    def __init__(self, initial, parent=None, dark=False):
        super().__init__(parent)
        self.dark_theme_enabled = bool(dark)
        self.current_color = QColor(initial) if isinstance(initial, QColor) else QColor("#ffffff")
        if not self.current_color.isValid():
            self.current_color = QColor("#ffffff")
        self._drag_active = False
        self._drag_pos = QPoint()
        self._updating_fields = False

        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setModal(True)
        self.setFixedSize(680, 500)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.panel = QFrame(self)
        self.panel.setObjectName("colorDialogPanel")
        root.addWidget(self.panel)

        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(24, 20, 24, 22)
        layout.setSpacing(18)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel(_color_dialog_title(parent))
        self.title_label.setObjectName("colorDialogTitle")
        header.addWidget(self.title_label)
        header.addStretch()
        self.close_btn = QPushButton()
        self.close_btn.setObjectName("dialogCloseButton")
        self.close_btn.setFixedSize(36, 36)
        self.close_btn.setIcon(_make_close_icon(self.dark_theme_enabled))
        self.close_btn.setIconSize(QSize(20, 20))
        self.close_btn.clicked.connect(self.reject)
        header.addWidget(self.close_btn)
        layout.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(20)
        picker_layout = QHBoxLayout()
        picker_layout.setSpacing(12)
        self.color_plane = ColorPlaneWidget(self)
        self.hue_slider = HueSliderWidget(self)
        picker_layout.addWidget(self.color_plane)
        picker_layout.addWidget(self.hue_slider)
        body.addLayout(picker_layout)

        controls = QVBoxLayout()
        controls.setSpacing(12)
        self.preview = QFrame()
        self.preview.setObjectName("colorPreview")
        self.preview.setFixedHeight(64)
        controls.addWidget(self.preview)

        self.hex_input = QLineEdit()
        self.hex_input.setObjectName("colorInput")
        self.hex_input.setMaxLength(7)
        self.hex_input.editingFinished.connect(self._hex_edited)
        controls.addLayout(self._field_row("HEX", self.hex_input))

        self.red_input = self._rgb_input()
        self.green_input = self._rgb_input()
        self.blue_input = self._rgb_input()
        controls.addLayout(self._field_row(self._text("red"), self.red_input))
        controls.addLayout(self._field_row(self._text("green"), self.green_input))
        controls.addLayout(self._field_row(self._text("blue"), self.blue_input))

        swatch_grid = QGridLayout()
        swatch_grid.setHorizontalSpacing(7)
        swatch_grid.setVerticalSpacing(8)
        swatches = ["#ffffff", "#111318", "#8b929d", "#2f343b", "#14d8c9", "#5e6bff", "#ff6868", "#ffd166"]
        for i, color in enumerate(swatches):
            btn = QPushButton()
            btn.setObjectName("swatchButton")
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(self._swatch_style(color))
            btn.clicked.connect(lambda checked=False, c=color: self._set_color(QColor(c)))
            swatch_grid.addWidget(btn, 0, i)
        controls.addLayout(swatch_grid)
        controls.addStretch()
        body.addLayout(controls, 1)
        layout.addLayout(body)

        actions = QHBoxLayout()
        actions.addStretch()
        self.ok_btn = QPushButton(self._action_text("ok"))
        self.ok_btn.setObjectName("dialogPrimaryButton")
        self.ok_btn.setFixedSize(118, 44)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton(self._action_text("cancel"))
        self.cancel_btn.setObjectName("dialogSecondaryButton")
        self.cancel_btn.setFixedSize(118, 44)
        self.cancel_btn.clicked.connect(self.reject)
        actions.addWidget(self.ok_btn)
        actions.addWidget(self.cancel_btn)
        layout.addLayout(actions)

        self.color_plane.colorChanged.connect(self._plane_changed)
        self.hue_slider.hueChanged.connect(self._hue_changed)
        self.red_input.editingFinished.connect(self._rgb_edited)
        self.green_input.editingFinished.connect(self._rgb_edited)
        self.blue_input.editingFinished.connect(self._rgb_edited)

        self._apply_theme()
        self._set_color(self.current_color)

    def _text(self, key):
        language = _resolve_language(self)
        labels = {
            "red": {"ru": "Красный", "en": "Red", "zh": "红色", "ja": "赤"},
            "green": {"ru": "Зелёный", "en": "Green", "zh": "绿色", "ja": "緑"},
            "blue": {"ru": "Синий", "en": "Blue", "zh": "蓝色", "ja": "青"},
        }
        return labels.get(key, {}).get(language, labels[key]["en"])

    def _action_text(self, action):
        language = _resolve_language(self)
        labels = {
            "ok": {"ru": "ОК", "en": "OK", "zh": "确定", "ja": "OK"},
            "cancel": {"ru": "Отмена", "en": "Cancel", "zh": "取消", "ja": "キャンセル"},
        }
        return labels.get(action, {}).get(language, labels[action]["en"])

    def _rgb_input(self):
        field = QLineEdit()
        field.setObjectName("colorInput")
        field.setValidator(QIntValidator(0, 255, field))
        field.setMaxLength(3)
        return field

    def _field_row(self, label_text, field):
        row = QHBoxLayout()
        row.setSpacing(10)
        label = QLabel(label_text)
        label.setObjectName("colorFieldLabel")
        label.setFixedWidth(68)
        row.addWidget(label)
        row.addWidget(field, 1)
        return row

    def _apply_theme(self):
        if self.dark_theme_enabled:
            self.setStyleSheet("""
                QDialog { background: transparent; }
                QFrame#colorDialogPanel {
                    background: rgba(17, 18, 21, 238);
                    border: 1px solid rgba(255, 255, 255, 34);
                    border-radius: 24px;
                }
                QLabel#colorDialogTitle {
                    color: #ffffff;
                    font: 750 16pt 'Segoe UI Variable';
                    background: transparent;
                }
                QLabel#colorFieldLabel {
                    color: rgba(255, 255, 255, 178);
                    font: 650 10pt 'Segoe UI Variable';
                    background: transparent;
                }
                QLineEdit#colorInput {
                    background: rgba(255, 255, 255, 0.075);
                    color: #f7f8fa;
                    border: 1px solid rgba(255, 255, 255, 0.10);
                    border-radius: 12px;
                    padding: 8px 10px;
                    font: 650 10pt 'Segoe UI Variable';
                    selection-background-color: #f7f8fa;
                    selection-color: #111318;
                }
                QLineEdit#colorInput:focus {
                    background: rgba(255, 255, 255, 0.11);
                    border-color: rgba(255, 255, 255, 0.22);
                }
                QPushButton {
                    background: rgba(255, 255, 255, 0.08);
                    color: #f7f8fa;
                    border: 1px solid rgba(255, 255, 255, 0.10);
                    border-radius: 14px;
                    font: 750 10.5pt 'Segoe UI Variable';
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.13);
                    border-color: rgba(255, 255, 255, 0.18);
                }
                QPushButton#dialogPrimaryButton {
                    background: #f7f8fa;
                    color: #111318;
                    border-color: rgba(255, 255, 255, 0.28);
                }
                QPushButton#dialogCloseButton {
                    background: transparent;
                    border: none;
                    border-radius: 12px;
                    padding: 0px;
                }
                QPushButton#dialogCloseButton:hover {
                    background: rgba(255, 255, 255, 0.10);
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background: transparent; }
                QFrame#colorDialogPanel {
                    background: rgba(255, 255, 255, 238);
                    border: 1px solid rgba(31, 35, 40, 28);
                    border-radius: 24px;
                }
                QLabel#colorDialogTitle {
                    color: #161a20;
                    font: 750 16pt 'Segoe UI Variable';
                    background: transparent;
                }
                QLabel#colorFieldLabel {
                    color: rgba(31, 35, 40, 180);
                    font: 650 10pt 'Segoe UI Variable';
                    background: transparent;
                }
                QLineEdit#colorInput {
                    background: rgba(255, 255, 255, 0.80);
                    color: #20242a;
                    border: 1px solid rgba(31, 35, 40, 0.10);
                    border-radius: 12px;
                    padding: 8px 10px;
                    font: 650 10pt 'Segoe UI Variable';
                    selection-background-color: #20242a;
                    selection-color: #ffffff;
                }
                QLineEdit#colorInput:focus {
                    background: #ffffff;
                    border-color: rgba(31, 35, 40, 0.20);
                }
                QPushButton {
                    background: rgba(255, 255, 255, 0.70);
                    color: #20242a;
                    border: 1px solid rgba(31, 35, 40, 0.10);
                    border-radius: 14px;
                    font: 750 10.5pt 'Segoe UI Variable';
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.95);
                    border-color: rgba(31, 35, 40, 0.16);
                }
                QPushButton#dialogPrimaryButton {
                    background: #20242a;
                    color: #ffffff;
                    border-color: rgba(31, 35, 40, 0.18);
                }
                QPushButton#dialogCloseButton {
                    background: transparent;
                    border: none;
                    border-radius: 12px;
                    padding: 0px;
                }
                QPushButton#dialogCloseButton:hover {
                    background: rgba(31, 35, 40, 0.07);
                }
            """)

    def _swatch_style(self, color):
        border = "rgba(255, 255, 255, 0.18)" if self.dark_theme_enabled else "rgba(31, 35, 40, 0.16)"
        return f"""
            QPushButton#swatchButton {{
                background: {color};
                border: 1px solid {border};
                border-radius: 10px;
            }}
            QPushButton#swatchButton:hover {{
                border: 2px solid {'rgba(255, 255, 255, 0.72)' if self.dark_theme_enabled else 'rgba(31, 35, 40, 0.42)'};
            }}
        """

    def _set_color(self, color):
        color = QColor(color)
        if not color.isValid():
            return
        self.current_color = color
        h, s, v = colorsys.rgb_to_hsv(color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
        self.hue_slider.set_hue(h)
        self.color_plane.set_hsv(h, s, v)
        self._sync_fields()

    def _sync_fields(self):
        self._updating_fields = True
        self.hex_input.setText(self.current_color.name())
        self.red_input.setText(str(self.current_color.red()))
        self.green_input.setText(str(self.current_color.green()))
        self.blue_input.setText(str(self.current_color.blue()))
        self.preview.setStyleSheet(f"""
            QFrame#colorPreview {{
                background: {self.current_color.name()};
                border: 1px solid {'rgba(255, 255, 255, 0.16)' if self.dark_theme_enabled else 'rgba(31, 35, 40, 0.12)'};
                border-radius: 18px;
            }}
        """)
        self._updating_fields = False

    def _plane_changed(self, color):
        if self._updating_fields:
            return
        self.current_color = color
        self._sync_fields()

    def _hue_changed(self, hue):
        if self._updating_fields:
            return
        self.color_plane.set_hsv(hue)
        r, g, b = colorsys.hsv_to_rgb(hue, self.color_plane.saturation, self.color_plane.value)
        self.current_color = QColor(int(r * 255), int(g * 255), int(b * 255))
        self._sync_fields()

    def _hex_edited(self):
        if self._updating_fields:
            return
        text = self.hex_input.text().strip()
        if text and not text.startswith("#"):
            text = f"#{text}"
        color = QColor(text)
        if color.isValid():
            self._set_color(color)
        else:
            self._sync_fields()

    def _rgb_edited(self):
        if self._updating_fields:
            return
        try:
            color = QColor(
                max(0, min(255, int(self.red_input.text() or 0))),
                max(0, min(255, int(self.green_input.text() or 0))),
                max(0, min(255, int(self.blue_input.text() or 0))),
            )
            self._set_color(color)
        except ValueError:
            self._sync_fields()

    def selected_color(self):
        return QColor(self.current_color)

    def showEvent(self, event):
        super().showEvent(event)
        _center_dialog_on_owner(self, self.parentWidget())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 64:
            self._drag_active = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_active = False


class ThemedTextInputDialog(QDialog):
    def __init__(self, parent, title, label, dark=False, value=""):
        super().__init__(parent)
        self.dark_theme_enabled = bool(dark)
        self._drag_active = False
        self._drag_pos = QPoint()

        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setModal(True)
        self.setFixedSize(430, 244)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.panel = QFrame(self)
        self.panel.setObjectName("inputDialogPanel")
        root.addWidget(self.panel)

        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(26, 20, 26, 24)
        layout.setSpacing(14)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("dialogTitle")
        header.addWidget(self.title_label)
        header.addStretch()
        self.close_btn = QPushButton()
        self.close_btn.setObjectName("dialogCloseButton")
        self.close_btn.setFixedSize(36, 36)
        self.close_btn.setIcon(_make_close_icon(self.dark_theme_enabled))
        self.close_btn.setIconSize(QSize(20, 20))
        self.close_btn.clicked.connect(self.reject)
        header.addWidget(self.close_btn)
        layout.addLayout(header)

        self.field_label = QLabel(label)
        self.field_label.setObjectName("dialogFieldLabel")
        layout.addWidget(self.field_label)

        self.input = QLineEdit()
        self.input.setText(value)
        self.input.setPlaceholderText(label)
        self.input.textChanged.connect(self._sync_ok_state)
        self.input.returnPressed.connect(self.accept)
        layout.addWidget(self.input)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 6, 0, 0)
        actions.setSpacing(10)
        actions.addStretch()
        self.ok_btn = QPushButton(self._action_text("ok"))
        self.ok_btn.setObjectName("dialogPrimaryButton")
        self.ok_btn.setFixedSize(120, 44)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton(self._action_text("cancel"))
        self.cancel_btn.setObjectName("dialogSecondaryButton")
        self.cancel_btn.setFixedSize(120, 44)
        self.cancel_btn.clicked.connect(self.reject)
        actions.addWidget(self.ok_btn)
        actions.addWidget(self.cancel_btn)
        layout.addLayout(actions)

        self._apply_theme()
        self._sync_ok_state(self.input.text())
        self.input.setFocus()
        self.input.selectAll()

    def _action_text(self, action):
        language = _resolve_language(self)
        labels = {
            "ok": {"ru": "ОК", "en": "OK", "zh": "确定", "ja": "OK"},
            "cancel": {"ru": "Отмена", "en": "Cancel", "zh": "取消", "ja": "キャンセル"},
        }
        return labels.get(action, {}).get(language, labels[action]["en"])

    def _apply_theme(self):
        if self.dark_theme_enabled:
            self.setStyleSheet("""
                QDialog {
                    background: transparent;
                }
                QFrame#inputDialogPanel {
                    background: rgba(17, 18, 21, 238);
                    border: 1px solid rgba(255, 255, 255, 34);
                    border-radius: 24px;
                }
                QLabel#dialogTitle {
                    color: #ffffff;
                    background: transparent;
                    font: 750 16pt 'Segoe UI Variable';
                }
                QLabel#dialogFieldLabel {
                    color: rgba(255, 255, 255, 178);
                    background: transparent;
                    font: 650 10.5pt 'Segoe UI Variable';
                }
                QLineEdit {
                    background: rgba(255, 255, 255, 0.075);
                    color: #f7f8fa;
                    border: 1px solid rgba(255, 255, 255, 0.10);
                    border-radius: 14px;
                    padding: 11px 14px;
                    font: 650 11pt 'Segoe UI Variable';
                    selection-background-color: #ffffff;
                    selection-color: #101010;
                }
                QLineEdit:focus {
                    border-color: rgba(255, 255, 255, 0.22);
                    background: rgba(255, 255, 255, 0.11);
                }
                QPushButton {
                    background: rgba(255, 255, 255, 0.08);
                    color: #f7f8fa;
                    border: 1px solid rgba(255, 255, 255, 0.10);
                    border-radius: 14px;
                    font: 750 10.5pt 'Segoe UI Variable';
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.13);
                    border-color: rgba(255, 255, 255, 0.18);
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.07);
                }
                QPushButton:disabled {
                    color: rgba(255, 255, 255, 90);
                    background: rgba(255, 255, 255, 0.04);
                    border-color: rgba(255, 255, 255, 0.07);
                }
                QPushButton#dialogPrimaryButton {
                    background: #f7f8fa;
                    color: #111318;
                    border-color: rgba(255, 255, 255, 0.28);
                }
                QPushButton#dialogPrimaryButton:hover {
                    background: #ffffff;
                    border-color: rgba(255, 255, 255, 0.40);
                }
                QPushButton#dialogPrimaryButton:disabled {
                    color: rgba(255, 255, 255, 90);
                    background: rgba(255, 255, 255, 0.04);
                    border-color: rgba(255, 255, 255, 0.07);
                }
                QPushButton#dialogCloseButton {
                    background: transparent;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    font: 16pt 'Segoe UI';
                    padding: 0px;
                }
                QPushButton#dialogCloseButton:hover {
                    background: rgba(255, 255, 255, 0.10);
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background: transparent;
                }
                QFrame#inputDialogPanel {
                    background: rgba(255, 255, 255, 238);
                    border: 1px solid rgba(31, 35, 40, 28);
                    border-radius: 24px;
                }
                QLabel#dialogTitle {
                    color: #161a20;
                    background: transparent;
                    font: 750 16pt 'Segoe UI Variable';
                }
                QLabel#dialogFieldLabel {
                    color: rgba(31, 35, 40, 180);
                    background: transparent;
                    font: 650 10.5pt 'Segoe UI Variable';
                }
                QLineEdit {
                    background: rgba(255, 255, 255, 0.80);
                    color: #20242a;
                    border: 1px solid rgba(31, 35, 40, 0.10);
                    border-radius: 14px;
                    padding: 11px 14px;
                    font: 650 11pt 'Segoe UI Variable';
                    selection-background-color: #232323;
                    selection-color: #ffffff;
                }
                QLineEdit:focus {
                    border-color: rgba(31, 35, 40, 0.20);
                    background: #ffffff;
                }
                QPushButton {
                    background: rgba(255, 255, 255, 0.70);
                    color: #20242a;
                    border: 1px solid rgba(31, 35, 40, 0.10);
                    border-radius: 14px;
                    font: 750 10.5pt 'Segoe UI Variable';
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.95);
                    border-color: rgba(31, 35, 40, 0.16);
                }
                QPushButton:pressed {
                    background: rgba(232, 235, 240, 0.95);
                }
                QPushButton:disabled {
                    color: rgba(31, 35, 40, 90);
                    background: rgba(232, 235, 240, 0.60);
                    border-color: rgba(31, 35, 40, 0.07);
                }
                QPushButton#dialogPrimaryButton {
                    background: #20242a;
                    color: #ffffff;
                    border-color: rgba(31, 35, 40, 0.18);
                }
                QPushButton#dialogPrimaryButton:hover {
                    background: #111318;
                    border-color: rgba(31, 35, 40, 0.24);
                }
                QPushButton#dialogPrimaryButton:disabled {
                    color: rgba(31, 35, 40, 90);
                    background: rgba(232, 235, 240, 0.60);
                    border-color: rgba(31, 35, 40, 0.07);
                }
                QPushButton#dialogCloseButton {
                    background: transparent;
                    color: #232323;
                    border: none;
                    border-radius: 8px;
                    font: 16pt 'Segoe UI';
                    padding: 0px;
                }
                QPushButton#dialogCloseButton:hover {
                    background: rgba(31, 35, 40, 0.07);
                }
            """)

    def _sync_ok_state(self, text):
        self.ok_btn.setEnabled(bool(text.strip()))

    def text_value(self):
        return self.input.text().strip()

    def showEvent(self, event):
        super().showEvent(event)
        _center_dialog_on_owner(self, self.parentWidget())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 58:
            self._drag_active = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_active = False


class TrailPreviewWidget(QWidget):
    def __init__(self, dialog, parent=None):
        super().__init__(parent)
        self.dialog = dialog
        self.phase = 0.0
        self.setMinimumHeight(132)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(40)

    def _tick(self):
        self.phase = (self.phase + 0.018) % 1.0
        self.update()

    def _settings(self):
        d = self.dialog
        colors = d.gradient_picker.get_colors() if hasattr(d, "gradient_picker") else getattr(d, "gradient_colors", ["#7f8792", "#ffffff"])
        return {
            "width": d.width_slider.value() if hasattr(d, "width_slider") else getattr(d, "trail_width", 8),
            "alpha": d.alpha_slider.value() if hasattr(d, "alpha_slider") else getattr(d, "alpha", 220),
            "fade": d.fade_switch.value if hasattr(d, "fade_switch") else getattr(d, "fade_enabled", True),
            "rgb": d.rgb_trail_switch.value if hasattr(d, "rgb_trail_switch") else getattr(d, "rgb_trail_enabled", False),
            "sakura": d.sakura_trail_switch.value if hasattr(d, "sakura_trail_switch") else getattr(d, "sakura_trail_enabled", False),
            "pixel": d.pixel_trail_switch.value if hasattr(d, "pixel_trail_switch") else getattr(d, "pixel_trail_enabled", False),
            "colors": colors or ["#7f8792", "#ffffff"],
        }

    def _mix_color(self, colors, t):
        if not colors:
            return QColor("#ffffff")
        qcolors = [QColor(color) for color in colors]
        if len(qcolors) == 1:
            return qcolors[0]
        segments = len(qcolors) - 1
        segment = min(int(t * segments), segments - 1)
        local_t = (t - segment / segments) * segments
        c1, c2 = qcolors[segment], qcolors[segment + 1]
        return QColor(
            int(c1.red() + (c2.red() - c1.red()) * local_t),
            int(c1.green() + (c2.green() - c1.green()) * local_t),
            int(c1.blue() + (c2.blue() - c1.blue()) * local_t),
        )

    def paintEvent(self, event):
        dark = getattr(self.dialog, "dark_theme_enabled", False)
        settings = self._settings()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        bg = QLinearGradient(rect.topLeft(), rect.bottomRight())
        if dark:
            bg.setColorAt(0.0, QColor(255, 255, 255, 24))
            bg.setColorAt(1.0, QColor(255, 255, 255, 7))
            border = QColor(255, 255, 255, 32)
            grid = QColor(255, 255, 255, 11)
        else:
            bg.setColorAt(0.0, QColor(255, 255, 255, 230))
            bg.setColorAt(1.0, QColor(238, 242, 247, 190))
            border = QColor(30, 34, 40, 26)
            grid = QColor(30, 34, 40, 12)
        painter.setPen(QPen(border, 1))
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, 22, 22)

        painter.setPen(QPen(grid, 1))
        for x in range(28, self.width(), 42):
            painter.drawLine(x, 22, x, self.height() - 22)
        for y in range(28, self.height(), 34):
            painter.drawLine(22, y, self.width() - 22, y)

        points = []
        usable_w = max(1, self.width() - 100)
        base_y = self.height() * 0.56
        for i in range(18):
            t = i / 17
            x = 50 + usable_w * t
            y = base_y + math.sin(t * math.pi * 2.1 + self.phase * math.pi * 2) * 22
            points.insert(0, QPointF(x, y))

        alpha = max(35, min(255, int(settings["alpha"])))
        width = max(2.0, min(24.0, settings["width"] * 0.65))
        denominator = max(1, len(points) - 1)

        if settings["sakura"]:
            for i, point in enumerate(points):
                t = i / denominator
                scale = 0.34 + 0.62 * (1 - t)
                petal_alpha = int(alpha * ((1 - t) ** 1.25 if settings["fade"] else 1.0))
                if petal_alpha <= 8:
                    continue
                painter.save()
                painter.translate(point)
                painter.rotate(-18 + i * 11)
                painter.setOpacity(petal_alpha / 255.0)
                image = SakuraPetal._emoji_image(18)
                size = 26 * scale
                painter.drawImage(QRectF(-size / 2, -size / 2, size, size), image, QRectF(0, 0, image.width(), image.height()))
                painter.restore()
        elif settings["pixel"]:
            for i, point in enumerate(points):
                t = i / denominator
                color = self._mix_color(settings["colors"], (t + self.phase) % 1.0 if settings["rgb"] else t)
                color.setAlpha(int(alpha * ((1 - t) ** 1.35 if settings["fade"] else 1.0)))
                size = max(4, int((width * 1.5) * (1 - t) + 3))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawRoundedRect(QRectF(point.x() - size / 2, point.y() - size / 2, size, size), 4, 4)
        else:
            for i in range(len(points) - 1):
                t = i / denominator
                color = self._mix_color(settings["colors"], (t + self.phase) % 1.0 if settings["rgb"] else t)
                color.setAlpha(int(alpha * ((1 - t) ** 1.35 if settings["fade"] else 1.0)))
                pen_width = width * (1 - t) + 2
                painter.setPen(QPen(color, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                painter.drawLine(points[i], points[i + 1])

        head = points[0]
        cursor_x = min(max(head.x(), 24), self.width() - 30)
        cursor_y = min(max(head.y(), 18), self.height() - 42)
        cursor_path = QPainterPath()
        cursor_path.moveTo(0, 0)
        cursor_path.lineTo(0, 24)
        cursor_path.lineTo(6.0, 18.4)
        cursor_path.lineTo(10.7, 27.0)
        cursor_path.lineTo(15.0, 24.8)
        cursor_path.lineTo(10.2, 16.2)
        cursor_path.lineTo(19.0, 16.2)
        cursor_path.closeSubpath()
        painter.save()
        painter.translate(cursor_x, cursor_y)
        if len(points) > 1:
            tail = points[1]
            direction = math.degrees(math.atan2(head.y() - tail.y(), head.x() - tail.x()))
            painter.rotate(direction + 135)
        painter.scale(0.82, 0.82)
        outline_pen = QPen(QColor(0, 0, 0, 135) if dark else QColor(255, 255, 255, 220), 3.2)
        outline_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(outline_pen)
        painter.setBrush(QColor("#ffffff" if dark else "#15181d"))
        painter.drawPath(cursor_path)
        painter.setPen(QPen(QColor(255, 255, 255, 235) if dark else QColor(0, 0, 0, 80), 1.0))
        painter.drawPath(cursor_path)
        painter.restore()


from light_theme import LightThemeMixin
from dark_theme import DarkThemeMixin

class SettingsDialog(QDialog, LightThemeMixin, DarkThemeMixin):
    settingsApplied = Signal(tuple)  # Новый сигнал

    def __init__(self, parent, trail_length, trail_width, gradient_colors, fade_enabled, alpha, glow_enabled, glow_color, outline_enabled, outline_color, rgb_trail_enabled, sakura_trail_enabled, current_language, pixel_trail_enabled, dark_theme_enabled):
        super().__init__(parent)
        self._drag_active = False
        self._drag_pos = None
        self.translations = parent.translations
        self.current_language = current_language
        self.tr = parent.tr
        self.dark_theme_enabled = dark_theme_enabled  # добавлено
        # copy profiles from parent so dialog shows existing saved profiles
        try:
            self._profiles = getattr(parent, '_profiles', {}) or {}
        except Exception:
            self._profiles = {}
        try:
            self.selected_profile = getattr(parent, 'selected_profile', None)
        except Exception:
            self.selected_profile = None
        # ensure a default profile named 'Стандартный' exists and is selected if nothing else
        try:
            if not self._profiles:
                default_name = "Стандартный"
                self._profiles = {default_name: [
                    trail_length, trail_width, self.gradient_colors,
                    fade_enabled, alpha, glow_enabled, glow_color,
                    outline_enabled, outline_color, rgb_trail_enabled,
                    sakura_trail_enabled, current_language, pixel_trail_enabled,
                    dark_theme_enabled
                ]}
                self.selected_profile = default_name
                # persist back to parent
                try:
                    parent._profiles = self._profiles
                    parent.selected_profile = default_name
                    if hasattr(parent, 'save_settings'):
                        parent.save_settings()
                except Exception:
                    pass
        except Exception:
            pass
        self.setWindowTitle(self.tr("settings"))
        self.setFixedSize(1040, 760)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Применяем тему через миксины
        if self.dark_theme_enabled:
            DarkThemeMixin.apply_theme(self)
            # Enable blurred translucent background
            try:
                self.enable_blur_background(self)
            except Exception:
                pass
        else:
            LightThemeMixin.apply_theme(self)
            try:
                self.enable_blur_background(self)
            except Exception:
                pass
        # --- Overlay для кросс-фейда между темами ---
        class CrossFadeOverlay(QWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                self.setGeometry(0, 0, parent.width(), parent.height())
                self._pixmap_old = None
                self._pixmap_new = None
                self._progress = 0.0
                self.hide()

            def setPixmaps(self, old, new):
                self._pixmap_old = old
                self._pixmap_new = new
                self.update()

            def getProgress(self):
                return self._progress

            def setProgress(self, value):
                self._progress = value
                self.update()

            progress = Property(float, fget=getProgress, fset=setProgress)

            def paintEvent(self, event):
                if self._pixmap_old and self._pixmap_new:
                    painter = QPainter(self)
                    painter.setOpacity(1.0)
                    painter.drawPixmap(0, 0, self._pixmap_old)
                    painter.setOpacity(self._progress)
                    painter.drawPixmap(0, 0, self._pixmap_new)
        self._theme_overlay = CrossFadeOverlay(self)
        self._theme_anim = None
        self._theme_overlay.raise_()
        self.trail_length = trail_length
        self.trail_width = trail_width
        self.gradient_colors = gradient_colors if gradient_colors else ["#3399ff", "#ffffff"]
        self.fade_enabled = fade_enabled
        self.alpha = alpha
        self.glow_enabled = glow_enabled
        self.glow_color = glow_color
        self.outline_enabled = outline_enabled
        self.outline_color = outline_color
        self.rgb_trail_enabled = rgb_trail_enabled  # Новый параметр
        self.sakura_trail_enabled = sakura_trail_enabled  # Новый параметр
        self.pixel_trail_enabled = pixel_trail_enabled  # Новый параметр

        # --- Главное горизонтальное разделение ---
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # --- Боковое меню ---
        self.menu_widget = QWidget()
        self.menu_widget.setFixedWidth(188)
        if self.dark_theme_enabled:
            DarkThemeMixin.apply_menu_style(self, self.menu_widget)
        else:
            LightThemeMixin.apply_menu_style(self, self.menu_widget)
        menu_layout = QVBoxLayout(self.menu_widget)
        menu_layout.setContentsMargins(14, 56, 14, 44)
        menu_layout.setSpacing(8)
        self.tab_buttons = []
        self.tab_icon_kinds = ["line", "effects", "profiles", "settings"]
        self.tabs = [self.tr("line"), self.tr("effects"), self.tr("profiles"), self.tr("settings_tab")]
        for i, name in enumerate(self.tabs):
            btn = QPushButton(name)
            btn.setIcon(self._tab_icon(self.tab_icon_kinds[i], selected=(i == 0)))
            btn.setIconSize(QSize(22, 22))
            btn.setFixedHeight(46)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setStyleSheet(self._tab_btn_style(selected=(i==0)))
            btn.clicked.connect(lambda checked, idx=i: self.select_tab(idx))
            menu_layout.addWidget(btn)
            self.tab_buttons.append(btn)
        self.active_indicator = QFrame(self.menu_widget)
        self.active_indicator.setObjectName("activeTabIndicator")
        self.active_indicator.setFixedSize(4, 34)
        self.active_indicator.setStyleSheet(
            "background: rgba(255, 255, 255, 0.85); border: none; border-radius: 2px;"
            if self.dark_theme_enabled else
            "background: rgba(31, 35, 40, 0.78); border: none; border-radius: 2px;"
        )
        self.active_indicator.raise_()
        menu_layout.addStretch()
        main_layout.addWidget(self.menu_widget)

        self.content_shell = QWidget()
        content_layout = QVBoxLayout(self.content_shell)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        self.preview_panel = TrailPreviewWidget(self)
        content_layout.addWidget(self.preview_panel)

        # --- Стек вкладок ---
        self.stacked = QStackedWidget()
        self.stacked.setObjectName("settingsStack")
        content_layout.addWidget(self.stacked, 1)
        main_layout.addWidget(self.content_shell, 1)

        # --- Вкладка 1: Линия (все существующие элементы) ---
        line_tab = QWidget()
        line_layout = QVBoxLayout(line_tab)
        line_layout.setContentsMargins(28, 26, 28, 28)
        line_layout.setSpacing(18)
        grid = QGridLayout()
        grid.setHorizontalSpacing(32)
        grid.setVerticalSpacing(18)
        label_width = 210  # Фиксированная ширина для всех лейблов

        lbl_trail_length = QLabel(self.tr("trail_length"))
        lbl_trail_length.setFixedWidth(label_width)
        grid.addWidget(lbl_trail_length, 0, 0)
        self.length_slider = QSlider(Qt.Orientation.Horizontal)
        self.length_slider.setMinimum(5)
        self.length_slider.setMaximum(100)
        self.length_slider.setValue(trail_length)
        grid.addWidget(self.length_slider, 0, 1)

        lbl_trail_width = QLabel(self.tr("trail_width"))
        lbl_trail_width.setFixedWidth(label_width)
        grid.addWidget(lbl_trail_width, 1, 0)
        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setMinimum(1)
        self.width_slider.setMaximum(40)
        self.width_slider.setValue(trail_width)
        grid.addWidget(self.width_slider, 1, 1)

        lbl_gradient = QLabel(self.tr("gradient"))
        lbl_gradient.setFixedWidth(label_width)
        grid.addWidget(lbl_gradient, 2, 0)
        self.gradient_picker = ColorGradientPicker(self.gradient_colors)
        grid.addWidget(self.gradient_picker, 2, 1)

        lbl_smooth_fade = QLabel(self.tr("smooth_fade"))
        lbl_smooth_fade.setFixedWidth(label_width)
        grid.addWidget(lbl_smooth_fade, 3, 0)
        grid.addLayout(self.setup_fade_setting(fade_enabled), 3, 1)

        lbl_transparency = QLabel(self.tr("transparency"))
        lbl_transparency.setFixedWidth(label_width)
        grid.addWidget(lbl_transparency, 4, 0)
        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setMinimum(10)
        self.alpha_slider.setMaximum(255)
        self.alpha_slider.setValue(alpha)
        grid.addWidget(self.alpha_slider, 4, 1)

        lbl_glow = QLabel(self.tr("glow"))
        lbl_glow.setFixedWidth(label_width)
        grid.addWidget(lbl_glow, 5, 0)
        glow_layout = QHBoxLayout()
        glow_layout.setContentsMargins(0, 0, 0, 0)
        glow_layout.setSpacing(0)
        self.glow_switch = ToggleSwitch(glow_enabled)
        self.glow_color_btn = QPushButton()
        self.glow_color_btn.setFixedSize(50, 36)
        self._set_color_button_style(self.glow_color_btn, glow_color)
        glow_layout.addWidget(self.glow_switch)
        glow_layout.addSpacing(8)
        glow_layout.addWidget(self.glow_color_btn)
        glow_layout.addStretch()
        glow_widget = QWidget()
        glow_widget.setLayout(glow_layout)
        grid.addWidget(glow_widget, 5, 1)

        lbl_outline = QLabel(self.tr("outline"))
        lbl_outline.setFixedWidth(label_width)
        grid.addWidget(lbl_outline, 6, 0)
        outline_layout = QHBoxLayout()
        outline_layout.setContentsMargins(0, 0, 0, 0)
        outline_layout.setSpacing(0)
        self.outline_switch = ToggleSwitch(outline_enabled)
        self.outline_color_btn = QPushButton()
        self.outline_color_btn.setFixedSize(50, 36)
        self._set_color_button_style(self.outline_color_btn, outline_color)
        outline_layout.addWidget(self.outline_switch)
        outline_layout.addSpacing(8)
        outline_layout.addWidget(self.outline_color_btn)
        outline_layout.addStretch()
        outline_widget = QWidget()
        outline_widget.setLayout(outline_layout)
        grid.addWidget(outline_widget, 6, 1)
        self.line_grid = grid
        line_card = QFrame()
        line_card.setObjectName("glassCard")
        line_card_layout = QVBoxLayout(line_card)
        line_card_layout.setContentsMargins(22, 22, 22, 22)
        line_card_layout.addLayout(grid)
        line_layout.addWidget(line_card)
        self.apply_btn = QPushButton(self.tr("apply"))
        self.apply_btn.setFixedHeight(56)
        # Стилизация через миксины
        # self.apply_btn.setStyleSheet(...)  # убрано, теперь через apply_theme
        self.apply_btn.clicked.connect(self.apply_settings)  # изменено
        line_layout.addWidget(self.apply_btn)
        self.stacked.addWidget(line_tab)

        # Подключаем сигналы выбора цвета только один раз
        self.glow_color_btn.clicked.connect(self.choose_glow_color)
        self.outline_color_btn.clicked.connect(self.choose_outline_color)

    # --- Вкладка 2: Эффекты (теперь с RGB трейлом, сакурой и пиксельным трейлом) ---
        effects_tab = QWidget()
        effects_layout = QVBoxLayout(effects_tab)
        effects_layout.setContentsMargins(28, 26, 28, 28)
        effects_layout.setSpacing(18)
        # --- RGB трейл ---
        rgb_layout = QHBoxLayout()
        rgb_layout.setSpacing(32)
        rgb_label = QLabel(self.tr("rgb_trail"))
        rgb_label.setStyleSheet("color: #232323; font: bold 16pt 'Segoe UI';")
        rgb_label.setFixedWidth(label_width)
        rgb_layout.addWidget(rgb_label)
        rgb_layout.addSpacing(0)
        # --- добавляем контейнер с отступом для переключателя ---
        rgb_switch_container = QWidget()
        rgb_switch_layout = QHBoxLayout(rgb_switch_container)
        rgb_switch_layout.setContentsMargins(0, 0, 0, 0)  # левый отступ 40px
        rgb_switch_layout.setSpacing(0)
        self.rgb_trail_switch = ToggleSwitch(self.rgb_trail_enabled)
        rgb_switch_layout.addWidget(self.rgb_trail_switch)
        rgb_layout.addWidget(rgb_switch_container)
        rgb_layout.addStretch()
        rgb_widget = QWidget()
        rgb_widget.setObjectName("optionRow")
        rgb_widget.setLayout(rgb_layout)
        # --- fix: выставляем отступы и spacing для rgb_layout сразу ---
        rgb_layout.setContentsMargins(18, 12, 18, 12)
        rgb_layout.setSpacing(32)
        effects_layout.addWidget(rgb_widget)
        # --- Sakura трейл ---
        sakura_layout = QHBoxLayout()
        sakura_layout.setSpacing(32)
        sakura_label = QLabel(self.tr("sakura_trail"))
        sakura_label.setStyleSheet("color: #232323; font: bold 16pt 'Segoe UI';")
        sakura_label.setFixedWidth(label_width)
        sakura_layout.addWidget(sakura_label)
        sakura_layout.addSpacing(0)
        # --- добавляем контейнер с отступом для переключателя ---
        sakura_switch_container = QWidget()
        sakura_switch_layout = QHBoxLayout(sakura_switch_container)
        sakura_switch_layout.setContentsMargins(0, 0, 0, 0)
        sakura_switch_layout.setSpacing(0)
        self.sakura_trail_switch = ToggleSwitch(self.sakura_trail_enabled)
        sakura_switch_layout.addWidget(self.sakura_trail_switch)
        sakura_layout.addWidget(sakura_switch_container)
        sakura_layout.addStretch()
        sakura_widget = QWidget()
        sakura_widget.setObjectName("optionRow")
        sakura_widget.setLayout(sakura_layout)
        # --- fix: выставляем отступы и spacing для sakura_layout сразу ---
        sakura_layout.setContentsMargins(18, 12, 18, 12)
        sakura_layout.setSpacing(32)
        effects_layout.addWidget(sakura_widget)
        # --- Pixel трейл ---
        pixel_layout = QHBoxLayout()
        pixel_layout.setSpacing(32)
        pixel_label = QLabel(self.tr("pixel_trail"))
        pixel_label.setStyleSheet("color: #232323; font: bold 16pt 'Segoe UI';")
        pixel_label.setFixedWidth(label_width)
        pixel_layout.addWidget(pixel_label)
        pixel_layout.addSpacing(0)
        self.pixel_trail_enabled = getattr(self, "pixel_trail_enabled", False)
        # --- добавляем контейнер с отступом для переключателя ---
        pixel_switch_container = QWidget()
        pixel_switch_layout = QHBoxLayout(pixel_switch_container)
        pixel_switch_layout.setContentsMargins(0, 0, 0, 0)
        pixel_switch_layout.setSpacing(0)
        self.pixel_trail_switch = ToggleSwitch(self.pixel_trail_enabled)
        pixel_switch_layout.addWidget(self.pixel_trail_switch)
        pixel_layout.addWidget(pixel_switch_container)
        pixel_layout.addStretch()
        pixel_widget = QWidget()
        pixel_widget.setObjectName("optionRow")
        pixel_widget.setLayout(pixel_layout)
        # --- fix: выставляем отступы и spacing для pixel_layout сразу ---
        pixel_layout.setContentsMargins(18, 12, 18, 12)
        pixel_layout.setSpacing(32)
        effects_layout.addWidget(pixel_widget)
        effects_layout.addStretch()
        self.apply_btn2 = QPushButton(self.tr("apply"))
        self.apply_btn2.setFixedHeight(56)
        # self.apply_btn2.setStyleSheet(...)  # убрано, теперь через apply_theme
        self.apply_btn2.clicked.connect(self.apply_settings)
        effects_layout.addWidget(self.apply_btn2)
        self.stacked.addWidget(effects_tab)


        # --- Вкладка: Профили (между эффектами и настройками) ---
        profiles_tab = QWidget()
        profiles_layout = QVBoxLayout(profiles_tab)
        profiles_layout.setContentsMargins(28, 26, 28, 28)
        profiles_layout.setSpacing(14)

        # Header: label + buttons on one row (aligned with other labels)
        profiles_label = QLabel(self.tr("profiles"))
        profiles_label.setFixedWidth(220)
        profiles_label.setStyleSheet("font: bold 18pt 'Segoe UI';")
        top_row = QHBoxLayout()
        top_row.addWidget(profiles_label)
        top_row.addStretch()
        profiles_layout.addLayout(top_row)

        # Use a combo box for profiles to match other dialogs
        self.profiles_combo = QComboBox()
        self.profiles_combo.setEditable(False)
        profiles_layout.addWidget(self.profiles_combo)

        # Buttons under the combo so text fits
        prof_row = QHBoxLayout()
        self.save_profile_btn = QPushButton(self.tr("save_profile"))
        self.delete_profile_btn = QPushButton(self.tr("delete_profile"))
        # make buttons a reasonable width so text fits
        try:
            self.save_profile_btn.setMinimumWidth(140)
            self.delete_profile_btn.setMinimumWidth(140)
        except Exception:
            pass
        prof_row.addWidget(self.save_profile_btn)
        prof_row.addWidget(self.delete_profile_btn)
        profiles_layout.addLayout(prof_row)

        self.save_profile_btn.clicked.connect(self.save_profile)
        self.delete_profile_btn.clicked.connect(self.delete_profile)

        # At bottom: Apply button for Profiles
        profiles_layout.addStretch()
        self.apply_profiles_btn = QPushButton(self.tr("apply"))
        self.apply_profiles_btn.setFixedHeight(56)
        self.apply_profiles_btn.clicked.connect(self.apply_settings)
        profiles_layout.addWidget(self.apply_profiles_btn)

        self.stacked.addWidget(profiles_tab)

        # --- Вкладка 3: Настройки ---
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.setContentsMargins(28, 26, 28, 28)
        settings_layout.setSpacing(18)
        lang_layout = QHBoxLayout()
        lang_layout.setSpacing(32)
        lang_label = QLabel(self.tr("language"))
        lang_label.setStyleSheet("color: #232323; font: bold 16pt 'Segoe UI';")
        lang_label.setFixedWidth(220)
        lang_layout.addWidget(lang_label)
        lang_layout.addSpacing(0)
        self.lang_combo = QComboBox()
        # Добавляем языки
        self.lang_map = {
            "ru": "Русский",
            "en": "English",
            "zh": "中文",
            "ja": "日本語"
        }
        for code, name in self.lang_map.items():
            self.lang_combo.addItem(name, code)
        # Устанавливаем текущий язык
        idx = list(self.lang_map.keys()).index(current_language) if current_language in self.lang_map else 0
        self.lang_combo.setCurrentIndex(idx)
        # Стилизация lang_combo теперь только через apply_theme миксинов
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        settings_layout.addLayout(lang_layout)

        # --- Выпадающий список для выбора темы (в стиле выбора языка) ---
        theme_layout = QHBoxLayout()
        theme_layout.setSpacing(32)
        self.theme_label = QLabel(self.tr("theme"))
        font = self.theme_label.font()
        font.setBold(True)
        font.setPointSize(16)
        self.theme_label.setFont(font)
        self.theme_label.setFixedWidth(220)
        theme_layout.addWidget(self.theme_label)
        theme_layout.addSpacing(0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItem(self.tr("theme_light"), False)
        self.theme_combo.addItem(self.tr("theme_dark"), True)
        self.theme_combo.setCurrentIndex(1 if self.dark_theme_enabled else 0)
        # Не задаём локальный стиль, чтобы работал глобальный стиль темы
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        settings_layout.addLayout(theme_layout)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_combo_changed)

        settings_layout.addStretch()
        self.apply_btn3 = QPushButton(self.tr("apply"))
        self.apply_btn3.setFixedHeight(56)
        # self.apply_btn3.setStyleSheet(...)  # убрано, теперь через apply_theme
        self.apply_btn3.clicked.connect(self.apply_settings)
        settings_layout.addWidget(self.apply_btn3)
        self.stacked.addWidget(settings_tab)

        # --- Добавляем версию справа снизу во вкладку "Настройки" ---
        self.version_label = QLabel("Version: 1.2", settings_tab)
        self.version_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.version_label.setStyleSheet("background: transparent;")
        self.version_label.adjustSize()
        self._update_version_label_style()
        self.version_label.raise_()
        self._move_version_label()

        # --- Применить стили ко всем элементам сразу после создания ---
        self._update_tab_labels_style()
        # populate profiles list from loaded settings
        try:
            # ensure we use parent's latest profiles (main app loaded them on startup)
            try:
                parent_profiles = getattr(self.parent(), '_profiles', None)
                if parent_profiles is not None:
                    self._profiles = parent_profiles or self._profiles
            except Exception:
                pass
            if hasattr(self, '_profiles'):
                self._refresh_profiles_list()
                # if no selected_profile, pick 'Стандартный' if present or first available
                try:
                    sel = getattr(self, 'selected_profile', None)
                    if not sel:
                        names = sorted(self.list_profiles())
                        if 'Стандартный' in names:
                            sel = 'Стандартный'
                        elif names:
                            sel = names[0]
                        if sel:
                            idx = self.profiles_combo.findText(sel)
                            if idx >= 0:
                                self.profiles_combo.setCurrentIndex(idx)
                                self.selected_profile = self.profiles_combo.currentText()
                except Exception:
                    pass
                # restore autosave checkbox and selection
                try:
                    if hasattr(self, 'autosave_chk'):
                        self.autosave_chk.setChecked(bool(getattr(self, 'autosave_profile', False)))
                    if hasattr(self, 'profiles_combo') and getattr(self, 'selected_profile', None):
                        idx = self.profiles_combo.findText(getattr(self, 'selected_profile', ''))
                        if idx >= 0:
                            self.profiles_combo.setCurrentIndex(idx)
                            self.selected_profile = self.profiles_combo.currentText()
                except Exception:
                    pass
        except Exception:
            pass
        self.glow_switch.set_dark_theme(self.dark_theme_enabled)
        self.outline_switch.set_dark_theme(self.dark_theme_enabled)
        self.fade_switch.set_dark_theme(self.dark_theme_enabled)
        self.rgb_trail_switch.set_dark_theme(self.dark_theme_enabled)
        self.sakura_trail_switch.set_dark_theme(self.dark_theme_enabled)
        self.pixel_trail_switch.set_dark_theme(self.dark_theme_enabled)
        self.gradient_picker.set_dark_theme(self.dark_theme_enabled)
        self._bind_preview_signals()
        self._apply_glass_chrome()
        QTimer.singleShot(0, lambda: self._move_active_indicator(self.stacked.currentIndex()))
        QTimer.singleShot(0, self._move_version_label)
        # Кнопки "Применить"
        # Кнопки "Применить" теперь стилизуются только через apply_theme миксинов
        # ComboBox (языки)
        # Стилизация lang_combo теперь только через apply_theme миксинов

        # --- Кнопка закрытия ---
        if not hasattr(self, 'close_btn'):
            self.close_btn = QPushButton(self)
            self.close_btn.clicked.connect(self.close)
        self.close_btn.setText("")
        self.close_btn.setIcon(_make_close_icon(self.dark_theme_enabled))
        self.close_btn.setIconSize(QSize(20, 20))
        self.close_btn.setFixedSize(36, 36)
        self.close_btn.move(self.width() - 58, 26)
        if self.dark_theme_enabled:
            DarkThemeMixin.apply_close_btn_style(self, self.close_btn)
        else:
            LightThemeMixin.apply_close_btn_style(self, self.close_btn)
        self.close_btn.raise_()
        self.close_btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.close_btn.setVisible(True)
        # --- Кастомная иконка шестерёнки (QLabel) ---
        if not hasattr(self, 'gear_label'):
            self.gear_label = QLabel(self)
            self.gear_label.setFixedSize(36, 36)
            self.gear_label.move(30, 28)
        if self.dark_theme_enabled:
            DarkThemeMixin.apply_gear_icon(self, self.gear_label)
        else:
            LightThemeMixin.apply_gear_icon(self, self.gear_label)
        self.gear_label.raise_()
        self.gear_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.gear_label.setVisible(True)
        # --- Подпись автора (QLabel) ---
        if not hasattr(self, 'author_label'):
            self.author_label = QLabel("by zxckurayami", self)
        if self.dark_theme_enabled:
            DarkThemeMixin.apply_author_label_style(self, self.author_label, self)
        else:
            LightThemeMixin.apply_author_label_style(self, self.author_label, self)
        self.author_label.raise_()
        self.author_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.author_label.setVisible(True)
        self.author_label.move(30, self.height() - self.author_label.height() - 30)

    def _bind_preview_signals(self):
        if not hasattr(self, "preview_panel"):
            return
        def refresh(*args):
            self.preview_panel.update()

        for widget in (
            getattr(self, "length_slider", None),
            getattr(self, "width_slider", None),
            getattr(self, "alpha_slider", None),
        ):
            if widget is not None:
                try:
                    widget.valueChanged.connect(refresh)
                except Exception:
                    pass

        for widget in (
            getattr(self, "fade_switch", None),
            getattr(self, "glow_switch", None),
            getattr(self, "outline_switch", None),
            getattr(self, "rgb_trail_switch", None),
            getattr(self, "sakura_trail_switch", None),
            getattr(self, "pixel_trail_switch", None),
        ):
            if widget is not None:
                try:
                    widget.valueChanged.connect(refresh)
                except Exception:
                    pass

        if hasattr(self, "gradient_picker"):
            try:
                self.gradient_picker.colorsChanged.connect(refresh)
            except Exception:
                pass

    def _set_color_button_style(self, button, color):
        border = "rgba(255, 255, 255, 0.18)" if getattr(self, "dark_theme_enabled", False) else "rgba(31, 35, 40, 0.14)"
        button.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            QPushButton:hover {{
                border: 1px solid {'rgba(255, 255, 255, 0.34)' if self.dark_theme_enabled else 'rgba(31, 35, 40, 0.26)'};
            }}
        """)

    def _apply_glass_chrome(self):
        dark = getattr(self, "dark_theme_enabled", False)
        stack_bg = "rgba(255, 255, 255, 0.055)" if dark else "rgba(255, 255, 255, 0.58)"
        stack_border = "rgba(255, 255, 255, 0.10)" if dark else "rgba(31, 35, 40, 0.08)"
        card_bg = "rgba(255, 255, 255, 0.060)" if dark else "rgba(255, 255, 255, 0.62)"
        card_border = "rgba(255, 255, 255, 0.10)" if dark else "rgba(31, 35, 40, 0.075)"
        self.stacked.setStyleSheet(f"""
            QStackedWidget#settingsStack {{
                background: {stack_bg};
                border: 1px solid {stack_border};
                border-radius: 24px;
            }}
            QFrame#glassCard, QWidget#optionRow {{
                background: {card_bg};
                border: 1px solid {card_border};
                border-radius: 20px;
            }}
        """)
        indicator = "rgba(255, 255, 255, 0.86)" if dark else "rgba(31, 35, 40, 0.78)"
        if hasattr(self, "active_indicator"):
            self.active_indicator.setStyleSheet(f"background: {indicator}; border: none; border-radius: 2px;")
        if hasattr(self, "glow_color_btn"):
            self._set_color_button_style(self.glow_color_btn, self.glow_color)
        if hasattr(self, "outline_color_btn"):
            self._set_color_button_style(self.outline_color_btn, self.outline_color)
        if hasattr(self, "preview_panel"):
            self.preview_panel.update()

    def _move_active_indicator(self, idx):
        if not hasattr(self, "active_indicator") or idx < 0 or idx >= len(getattr(self, "tab_buttons", [])):
            return
        btn = self.tab_buttons[idx]
        y = btn.y() + (btn.height() - self.active_indicator.height()) // 2
        self.active_indicator.move(10, y)
        self.active_indicator.raise_()

    # --- Profiles methods (moved inside SettingsDialog) ---
    def list_profiles(self):
        return list(getattr(self, '_profiles', {}).keys())

    def save_profile(self):
        dlg = ThemedTextInputDialog(
            self,
            self.tr('save_profile'),
            self.tr('profile_name'),
            getattr(self, 'dark_theme_enabled', False)
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        name = dlg.text_value()
        if not name:
            return
        profiles = getattr(self, '_profiles', {})
        profiles[name] = self.get_settings()
        self._profiles = profiles
        # persist via parent if available
        if hasattr(self.parent(), 'save_settings'):
            # also update parent storage
            try:
                self.parent()._profiles = self._profiles
                self.parent().save_settings()
            except Exception:
                pass
        # refresh combobox and select the new profile
        self._refresh_profiles_list()
        try:
            idx = self.profiles_combo.findText(name)
            if idx >= 0:
                self.profiles_combo.setCurrentIndex(idx)
                self.selected_profile = name
        except Exception:
            pass
        # Immediately apply saved profile to the app
        try:
            settings = self._profiles.get(name)
            if settings and hasattr(self, 'settingsApplied'):
                # emit the profile tuple so main app applies it
                self.settingsApplied.emit(settings)
        except Exception:
            logger.exception('Failed to apply newly saved profile')

    def load_profile(self):
        name = self.profiles_combo.currentText() if hasattr(self, 'profiles_combo') else None
        if not name:
            return
        profiles = getattr(self, '_profiles', {})
        settings = profiles.get(name)
        if not settings:
            return
        (new_trail_length, new_trail_width, new_gradient_colors,
         new_fade_enabled, new_alpha, new_glow_enabled, new_glow_color,
         new_outline_enabled, new_outline_color, new_rgb_trail_enabled,
         new_sakura_trail_enabled, new_language, new_pixel_trail_enabled,
         new_dark_theme_enabled) = settings
        # Update controls
        self.length_slider.setValue(new_trail_length)
        self.width_slider.setValue(new_trail_width)
        self.gradient_picker.set_colors(new_gradient_colors)
        try:
            self.fade_switch.setValue(new_fade_enabled)
        except Exception:
            try:
                self.fade_switch.value = new_fade_enabled
            except Exception:
                pass
        self.alpha_slider.setValue(new_alpha)
        try:
            self.glow_switch.setValue(new_glow_enabled)
        except Exception:
            try:
                self.glow_switch.value = new_glow_enabled
            except Exception:
                pass
        self.glow_color = new_glow_color
        self._set_color_button_style(self.glow_color_btn, self.glow_color)
        try:
            self.outline_switch.setValue(new_outline_enabled)
        except Exception:
            try:
                self.outline_switch.value = new_outline_enabled
            except Exception:
                pass
        self.outline_color = new_outline_color
        self._set_color_button_style(self.outline_color_btn, self.outline_color)
        # switches update theme-sensitive visuals
        self.rgb_trail_switch.set_dark_theme(self.dark_theme_enabled)
        self.sakura_trail_switch.set_dark_theme(self.dark_theme_enabled)
        self.pixel_trail_switch.set_dark_theme(self.dark_theme_enabled)
        # language
        try:
            idx = list(self.lang_map.keys()).index(new_language) if new_language in self.lang_map else 0
            self.lang_combo.setCurrentIndex(idx)
        except Exception:
            pass
        # theme
        self.theme_combo.setCurrentIndex(1 if new_dark_theme_enabled else 0)
        # mark selected profile but do not auto-apply
        self.selected_profile = name

    def delete_profile(self):
        name = self.profiles_combo.currentText() if hasattr(self, 'profiles_combo') else None
        if not name:
            return
        profiles = getattr(self, '_profiles', {})
        if name in profiles:
            del profiles[name]
            self._profiles = profiles
            if hasattr(self.parent(), 'save_settings'):
                try:
                    self.parent()._profiles = self._profiles
                    self.parent().save_settings()
                except Exception:
                    pass
            self._refresh_profiles_list()

    def _refresh_profiles_list(self):
        try:
            self.profiles_combo.blockSignals(True)
            self.profiles_combo.clear()
            names = sorted(self.list_profiles())
            if not names:
                self.profiles_combo.addItem(self.tr("(no_profiles)"))
                self.profiles_combo.setEnabled(False)
            else:
                for name in names:
                    self.profiles_combo.addItem(name)
                self.profiles_combo.setEnabled(True)
            # restore previous selection if available
            sel = getattr(self, 'selected_profile', None)
            if sel:
                idx = self.profiles_combo.findText(sel)
                if idx >= 0:
                    self.profiles_combo.setCurrentIndex(idx)
            # connect selection change to update selected_profile
            try:
                self.profiles_combo.currentIndexChanged.connect(lambda idx: setattr(self, 'selected_profile', self.profiles_combo.currentText()))
            except Exception:
                pass
            self.profiles_combo.blockSignals(False)
        except Exception:
            logger.exception('Failed to refresh profiles combo')

    def on_theme_combo_changed(self, idx):
        # Получаем значение из data (True/False)
        value = self.theme_combo.itemData(idx)
        if value != self.dark_theme_enabled:
            self.toggle_theme(value)

    def toggle_theme(self, enabled=None):
        # --- Плавная анимация смены темы ---
        if enabled is None:
            new_theme = not self.dark_theme_enabled
        else:
            new_theme = enabled
        if new_theme == self.dark_theme_enabled:
            return  # Нет смены
        # --- Кросс-фейд между темами ---
        # 1. Скриншот старой темы
        old_pixmap = self.grab()
        # 2. Меняем тему (но не показываем overlay)
        self.dark_theme_enabled = new_theme
        if hasattr(self, 'theme_combo'):
            self.theme_combo.setStyleSheet("")
        if hasattr(self, 'theme_label'):
            self.theme_label.setStyleSheet("")
        if hasattr(self, 'close_btn') and hasattr(self, 'menu_widget') and hasattr(self, 'gear_label') and hasattr(self, 'author_label'):
            if self.dark_theme_enabled:
                DarkThemeMixin.apply_theme(self)
                DarkThemeMixin.apply_menu_style(self, self.menu_widget)
                DarkThemeMixin.apply_close_btn_style(self, self.close_btn)
                DarkThemeMixin.apply_gear_icon(self, self.gear_label)
                DarkThemeMixin.apply_author_label_style(self, self.author_label, self)
            else:
                LightThemeMixin.apply_theme(self)
                LightThemeMixin.apply_menu_style(self, self.menu_widget)
                LightThemeMixin.apply_close_btn_style(self, self.close_btn)
                LightThemeMixin.apply_gear_icon(self, self.gear_label)
                LightThemeMixin.apply_author_label_style(self, self.author_label, self)
        if self.theme_combo.currentIndex() != (1 if self.dark_theme_enabled else 0):
            self.theme_combo.setCurrentIndex(1 if self.dark_theme_enabled else 0)
        self._update_tab_labels_style()
        self.glow_switch.set_dark_theme(self.dark_theme_enabled)
        self.outline_switch.set_dark_theme(self.dark_theme_enabled)
        self.fade_switch.set_dark_theme(self.dark_theme_enabled)
        self.rgb_trail_switch.set_dark_theme(self.dark_theme_enabled)
        self.sakura_trail_switch.set_dark_theme(self.dark_theme_enabled)
        self.pixel_trail_switch.set_dark_theme(self.dark_theme_enabled)
        self.gradient_picker.set_dark_theme(self.dark_theme_enabled)
        self._apply_glass_chrome()
        if hasattr(self.parent(), 'save_settings'):
            self.parent().dark_theme_enabled = self.dark_theme_enabled
            self.parent().save_settings()
        # --- Обновить стиль version_label при смене темы ---
        self._update_version_label_style()
        # --- Кнопка закрытия ---
        if not hasattr(self, 'close_btn'):
            self.close_btn = QPushButton(self)
            self.close_btn.clicked.connect(self.close)
        self.close_btn.setText("")
        self.close_btn.setIcon(_make_close_icon(self.dark_theme_enabled))
        self.close_btn.setIconSize(QSize(20, 20))
        self.close_btn.setFixedSize(36, 36)
        self.close_btn.move(self.width() - 58, 26)
        if self.dark_theme_enabled:
            DarkThemeMixin.apply_close_btn_style(self, self.close_btn)
        else:
            LightThemeMixin.apply_close_btn_style(self, self.close_btn)
        self.close_btn.raise_()
        self.close_btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.close_btn.setVisible(True)
        # --- Кастомная иконка шестерёнки (QLabel) ---
        if not hasattr(self, 'gear_label'):
            self.gear_label = QLabel(self)
            self.gear_label.setFixedSize(36, 36)
            self.gear_label.move(30, 28)
        if self.dark_theme_enabled:
            DarkThemeMixin.apply_gear_icon(self, self.gear_label)
        else:
            LightThemeMixin.apply_gear_icon(self, self.gear_label)
        self.gear_label.raise_()
        self.gear_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.gear_label.setVisible(True)
        # --- Подпись автора (QLabel) ---
        if not hasattr(self, 'author_label'):
            self.author_label = QLabel("by zxckurayami", self)
        if self.dark_theme_enabled:
            DarkThemeMixin.apply_author_label_style(self, self.author_label, self)
        else:
            LightThemeMixin.apply_author_label_style(self, self.author_label, self)
        self.author_label.raise_()
        self.author_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.author_label.setVisible(True)
        self.author_label.move(30, self.height() - self.author_label.height() - 30)
        # --- Сигналы больше не подключаем здесь ---
        self._drag_active = False
        self._drag_pos = None
        self.select_tab(self.stacked.currentIndex())
        # 3. Скриншот новой темы
        new_pixmap = self.grab()
        # 4. Кросс-фейд анимация
        self._theme_overlay.setGeometry(0, 0, self.width(), self.height())
        self._theme_overlay.setPixmaps(old_pixmap, new_pixmap)
        self._theme_overlay.setProgress(0.0)
        self._theme_overlay.raise_()  # Overlay всегда поверх всех элементов
        self._theme_overlay.show()
        anim = QPropertyAnimation(self._theme_overlay, b"progress", self)
        anim.setDuration(400)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._theme_anim = anim
        def after_fade():
            self._theme_overlay.hide()
        anim.finished.connect(after_fade)
        anim.start()
        self._theme_anim = anim

    def _tab_btn_style(self, selected=False):
        if getattr(self, "dark_theme_enabled", False):
            return DarkThemeMixin.tab_btn_style(self, selected)
        else:
            return LightThemeMixin.tab_btn_style(self, selected)

    def _tab_icon(self, kind, selected=False):
        dark = getattr(self, "dark_theme_enabled", False)
        if selected:
            color = QColor("#ffffff" if dark else "#161a20")
        else:
            color = QColor(255, 255, 255, 178) if dark else QColor(31, 35, 40, 166)

        pix = QPixmap(24, 24)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(color, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if kind == "line":
            path = QPainterPath()
            path.moveTo(4, 15)
            path.cubicTo(8, 7, 14, 18, 20, 9)
            painter.drawPath(path)
            painter.drawEllipse(QPointF(19.2, 8.8), 1.8, 1.8)
        elif kind == "effects":
            painter.drawLine(12, 4, 12, 8)
            painter.drawLine(12, 16, 12, 20)
            painter.drawLine(4, 12, 8, 12)
            painter.drawLine(16, 12, 20, 12)
            painter.drawLine(7.5, 7.5, 9.4, 9.4)
            painter.drawLine(14.6, 14.6, 16.5, 16.5)
            painter.drawLine(16.5, 7.5, 14.6, 9.4)
            painter.drawLine(9.4, 14.6, 7.5, 16.5)
        elif kind == "profiles":
            painter.drawRoundedRect(QRectF(5, 4, 14, 16), 4, 4)
            painter.drawLine(8.5, 9, 15.5, 9)
            painter.drawLine(8.5, 13, 15.5, 13)
            painter.drawLine(8.5, 17, 13.2, 17)
        else:
            painter.drawEllipse(QPointF(12, 12), 5.2, 5.2)
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                inner = QPointF(12 + math.cos(rad) * 8.1, 12 + math.sin(rad) * 8.1)
                outer = QPointF(12 + math.cos(rad) * 10.1, 12 + math.sin(rad) * 10.1)
                painter.drawLine(inner, outer)

        painter.end()
        return QIcon(pix)

    def select_tab(self, idx):
        # Update tab button states/styles
        for i, btn in enumerate(self.tab_buttons):
            selected = i == idx
            btn.setChecked(selected)
            btn.setStyleSheet(self._tab_btn_style(selected=selected))
            if hasattr(self, "tab_icon_kinds") and i < len(self.tab_icon_kinds):
                btn.setIcon(self._tab_icon(self.tab_icon_kinds[i], selected=selected))
                btn.setIconSize(QSize(22, 22))
        self._move_active_indicator(idx)

        current_idx = self.stacked.currentIndex()
        if current_idx == idx:
            return
        self.stacked.setCurrentIndex(idx)
        self._update_tab_labels_style()
        if idx == 3 and hasattr(self, "version_label"):
            QTimer.singleShot(0, self._move_version_label)
        if hasattr(self, "preview_panel"):
            self.preview_panel.update()

    def _update_tab_labels_style(self):
        label_color = "#f6f7f9" if self.dark_theme_enabled else "#20242a"
        font = "font: 650 12pt 'Segoe UI Variable';"
        # Вкладка 1
        grid = self.line_grid
        for row in range(7):
            lbl = grid.itemAtPosition(row, 0).widget()
            lbl.setStyleSheet(f"color: {label_color}; {font}")
        # Вкладка 2
        for i in range(3):
            eff_layout = self.stacked.widget(1).layout().itemAt(i).widget().layout()
            lbl = eff_layout.itemAt(0).widget()
            lbl.setStyleSheet(f"color: {label_color}; {font}")
        # Вкладка 3 (Settings is now index 3 due to Profiles tab)
        lang_layout = self.stacked.widget(3).layout().itemAt(0).layout()
        lang_label = lang_layout.itemAt(0).widget()
        lang_label.setStyleSheet(f"color: {label_color}; {font}")
        # Profiles header label (it's inside the profiles tab as top widget)
        try:
            profiles_tab = self.stacked.widget(2)
            # first item in profiles tab layout is the top_row layout
            top_row = profiles_tab.layout().itemAt(0).layout()
            profiles_lbl = top_row.itemAt(0).widget()
            if profiles_lbl is not None:
                profiles_lbl.setStyleSheet(f"color: {label_color}; font: 750 18pt 'Segoe UI Variable';")
        except Exception:
            pass

    def _move_version_label(self):
        settings_tab = self.stacked.widget(3)
        if hasattr(self, 'version_label') and self.version_label.parent() is settings_tab:
            w = max(settings_tab.width(), self.stacked.width())
            label_w = self.version_label.width()
            label_h = self.version_label.height()
            x = max(28, w - label_w - 64)
            apply_y = self.apply_btn3.y() if hasattr(self, "apply_btn3") else 0
            y = apply_y - label_h - 26 if apply_y > 0 else settings_tab.height() - label_h - 94
            self.version_label.move(x, max(28, y))

    def _update_version_label_style(self):
        # Применяем стиль к version_label в зависимости от темы
        if getattr(self, "dark_theme_enabled", False):
            self.version_label.setStyleSheet("color: #fff; font: 10pt 'Segoe UI'; background: transparent;")
        else:
            self.version_label.setStyleSheet("color: #232323; font: 10pt 'Segoe UI'; background: transparent;")
        self.version_label.adjustSize()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Перемещаем подпись автора при изменении размера окна
        if hasattr(self, 'author_label'):
            self.author_label.move(30, self.height() - self.author_label.height() - 30)
        if hasattr(self, 'close_btn'):
            self.close_btn.move(self.width() - 58, 26)
        if hasattr(self, 'active_indicator'):
            self._move_active_indicator(self.stacked.currentIndex())
        if hasattr(self, 'version_label'):
            self._move_version_label()
        # Overlay всегда на весь диалог
        if hasattr(self, '_theme_overlay'):
            self._theme_overlay.setGeometry(0, 0, self.width(), self.height())

    def paintEvent(self, event):
        if self.dark_theme_enabled:
            DarkThemeMixin.paintEvent(self, event, self)
        else:
            LightThemeMixin.paintEvent(self, event, self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_active = False

    def choose_glow_color(self):
        color = themed_get_color(QColor(self.glow_color), self, getattr(self, 'dark_theme_enabled', False))
        if color.isValid():
            self.glow_color = color.name()
            self._set_color_button_style(self.glow_color_btn, self.glow_color)
            if hasattr(self, "preview_panel"):
                self.preview_panel.update()

    def choose_outline_color(self):
        color = themed_get_color(QColor(self.outline_color), self, getattr(self, 'dark_theme_enabled', False))
        if color.isValid():
            self.outline_color = color.name()
            self._set_color_button_style(self.outline_color_btn, self.outline_color)
            if hasattr(self, "preview_panel"):
                self.preview_panel.update()

    # apply_theme теперь берётся из LightThemeMixin/DarkThemeMixin

    def get_settings(self):
        return (
            self.length_slider.value(),
            self.width_slider.value(),
            self.gradient_picker.get_colors(),
            self.fade_switch.value,
            self.alpha_slider.value(),
            self.glow_switch.value,
            self.glow_color,
            self.outline_switch.value,
            self.outline_color,
            self.rgb_trail_switch.value,
            self.sakura_trail_switch.value,
            self.lang_combo.currentData(),
            self.pixel_trail_switch.value,
            self.dark_theme_enabled
        )
    

    def setup_fade_setting(self, enabled):
        layout = QHBoxLayout()
        layout.setSpacing(12)
        self.fade_switch = ToggleSwitch(enabled)
        layout.addWidget(self.fade_switch)
        layout.addStretch()
        return layout

    def apply_settings(self):
        # Determine who called Apply
        sender = None
        try:
            sender = self.sender()
        except Exception:
            sender = None
        # If Apply pressed on Profiles tab -> apply currently selected profile to the app
        if sender is not None and hasattr(self, 'apply_profiles_btn') and sender == self.apply_profiles_btn:
            name = self.profiles_combo.currentText() if hasattr(self, 'profiles_combo') else None
            if not name:
                return
            profiles = getattr(self, '_profiles', {})
            settings = profiles.get(name)
            if not settings:
                return
            # Emit the saved settings tuple directly
            try:
                self.settingsApplied.emit(settings)
                # persist selected profile choice
                if hasattr(self.parent(), 'save_settings'):
                    try:
                        self.parent().selected_profile = name
                        self.parent()._profiles = self._profiles
                        self.parent().save_settings()
                    except Exception:
                        pass
            except Exception:
                logger.exception('Failed to apply profile')
            return

        # Default: Apply current UI settings to app and save into selected profile if any
        try:
            settings = self.get_settings()
            self.settingsApplied.emit(settings)
            name = getattr(self, 'selected_profile', None)
            if not name and hasattr(self, 'profiles_combo'):
                name = self.profiles_combo.currentText()
            if name:
                profiles = getattr(self, '_profiles', {})
                profiles[name] = settings
                self._profiles = profiles
                if hasattr(self.parent(), 'save_settings'):
                    try:
                        self.parent()._profiles = self._profiles
                        self.parent().selected_profile = name
                        self.parent().save_settings()
                    except Exception:
                        pass
        except Exception:
            logger.exception('Apply settings failed')

    def update_language(self, translations, lang_code):
        self.translations = translations
        self.current_language = lang_code
        self.tr = lambda key: self.translations.get(self.current_language, {}).get(key, key)
        # Обновить названия вкладок (insert profiles before settings)
        self.tabs = [self.tr("line"), self.tr("effects"), self.tr("profiles"), self.tr("settings_tab")]
        for i, btn in enumerate(self.tab_buttons):
            selected = i == self.stacked.currentIndex()
            btn.setText(self.tabs[i])
            btn.setStyleSheet(self._tab_btn_style(selected=selected))
            if hasattr(self, "tab_icon_kinds") and i < len(self.tab_icon_kinds):
                btn.setIcon(self._tab_icon(self.tab_icon_kinds[i], selected=selected))
                btn.setIconSize(QSize(22, 22))
        # Обновить все подписи и кнопки
        # Вкладка 1
        grid = self.line_grid
        grid.itemAtPosition(0, 0).widget().setText(self.tr("trail_length"))
        grid.itemAtPosition(0, 0).widget().setFixedWidth(220)
        grid.itemAtPosition(1, 0).widget().setText(self.tr("trail_width"))
        grid.itemAtPosition(1, 0).widget().setFixedWidth(220)
        grid.itemAtPosition(2, 0).widget().setText(self.tr("gradient"))
        grid.itemAtPosition(2, 0).widget().setFixedWidth(220)
        grid.itemAtPosition(3, 0).widget().setText(self.tr("smooth_fade"))
        grid.itemAtPosition(3, 0).widget().setFixedWidth(220)
        grid.itemAtPosition(4, 0).widget().setText(self.tr("transparency"))
        grid.itemAtPosition(4, 0).widget().setFixedWidth(220)
        grid.itemAtPosition(5, 0).widget().setText(self.tr("glow"))
        grid.itemAtPosition(5, 0).widget().setFixedWidth(220)
        grid.itemAtPosition(6, 0).widget().setText(self.tr("outline"))
        grid.itemAtPosition(6, 0).widget().setFixedWidth(220)
        self.apply_btn.setText(self.tr("apply"))
        # Вкладка 2
        effects_layout = self.stacked.widget(1).layout()
        rgb_widget = effects_layout.itemAt(0).widget()
        rgb_label = rgb_widget.layout().itemAt(0).widget()
        rgb_label.setText(self.tr("rgb_trail"))
        rgb_label.setFixedWidth(220)
        sakura_widget = effects_layout.itemAt(1).widget()
        sakura_label = sakura_widget.layout().itemAt(0).widget()
        sakura_label.setText(self.tr("sakura_trail"))
        sakura_label.setFixedWidth(220)
        # Вкладка Профили
        try:
            profiles_widget = self.stacked.widget(2)
            # Header label is the first item in the top row layout
            top_row = profiles_widget.layout().itemAt(0).layout()
            header_label = top_row.itemAt(0).widget()
            header_label.setText(self.tr("profiles"))
            header_label.setFixedWidth(220)
            # Update combo placeholder text if empty
            try:
                if self.profiles_combo.count() == 0:
                    self.profiles_combo.addItem(self.tr("(no_profiles)"))
            except Exception:
                pass
            # Buttons
            if hasattr(self, 'save_profile_btn'):
                self.save_profile_btn.setText(self.tr("save_profile"))
            if hasattr(self, 'delete_profile_btn'):
                self.delete_profile_btn.setText(self.tr("delete_profile"))
            if hasattr(self, 'apply_profiles_btn'):
                self.apply_profiles_btn.setText(self.tr("apply"))
        except Exception:
            pass
        pixel_widget = effects_layout.itemAt(2).widget()
        pixel_label = pixel_widget.layout().itemAt(0).widget()
        pixel_label.setText(self.tr("pixel_trail"))
        pixel_label.setFixedWidth(220)
        self.apply_btn2.setText(self.tr("apply"))
        # Вкладка 3
        settings_layout = self.stacked.widget(3).layout()
        lang_label = settings_layout.itemAt(0).layout().itemAt(0).widget()
        lang_label.setText(self.tr("language"))
        lang_label.setFixedWidth(220)
        self.apply_btn3.setText(self.tr("apply"))
        # Обновить лейбл и переводы для выбора темы
        self.theme_label.setText(self.tr("theme"))
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        self.theme_combo.addItem(self.tr("theme_light"), False)
        self.theme_combo.addItem(self.tr("theme_dark"), True)
        self.theme_combo.setCurrentIndex(1 if self.dark_theme_enabled else 0)
        self.theme_combo.blockSignals(False)
        # Заголовок окна
        self.setWindowTitle(self.tr("settings"))
        # --- ВОССТАНАВЛИВАЕМ ОТСТУПЫ ТОЛЬКО ДЛЯ КОНКРЕТНЫХ layout'ов ---
        # Glow
        glow_widget = grid.itemAtPosition(5, 1).widget()
        if glow_widget is not None and isinstance(glow_widget.layout(), QHBoxLayout):
            glow_widget.layout().setContentsMargins(0, 0, 0, 0)
            glow_widget.layout().setSpacing(0)
        # Outline
        outline_widget = grid.itemAtPosition(6, 1).widget()
        if outline_widget is not None and isinstance(outline_widget.layout(), QHBoxLayout):
            outline_widget.layout().setContentsMargins(0, 0, 0, 0)
            outline_widget.layout().setSpacing(0)
        # --- ВОССТАНАВЛИВАЕМ ОТСТУПЫ ТОЛЬКО ДЛЯ КНОПОК В ЭФФЕКТАХ ---
        # RGB трейл
        rgb_widget = effects_layout.itemAt(0).widget()
        if rgb_widget is not None and isinstance(rgb_widget.layout(), QHBoxLayout):
            rgb_widget.layout().setContentsMargins(18, 12, 18, 12)
            rgb_widget.layout().setSpacing(32)
        # Sakura трейл
        sakura_widget = effects_layout.itemAt(1).widget()
        if sakura_widget is not None and isinstance(sakura_widget.layout(), QHBoxLayout):
            sakura_widget.layout().setContentsMargins(18, 12, 18, 12)
            sakura_widget.layout().setSpacing(32)
        # Pixel трейл
        pixel_widget = effects_layout.itemAt(2).widget()
        if pixel_widget is not None and isinstance(pixel_widget.layout(), QHBoxLayout):
            pixel_widget.layout().setContentsMargins(18, 12, 18, 12)
            pixel_widget.layout().setSpacing(32)

class SakuraPetal:
    _emoji_cache = {}

    def __init__(self, pos, base_size):
        self.x, self.y = float(pos.x()), float(pos.y())
        self.size = random.uniform(base_size * 0.85, base_size * 1.2)
        drift_angle = random.uniform(0, 2 * math.pi)
        drift_speed = random.uniform(0.08, 0.38)
        self.vx = math.cos(drift_angle) * drift_speed
        self.vy = math.sin(drift_angle) * drift_speed
        self.rotation = random.uniform(0, 2 * math.pi)
        self.rotation_speed = random.uniform(-0.055, 0.055)
        self.life = random.randint(34, 58)
        self.age = 0
        self.opacity = 1.0
        self.scale = 1.0
        self.sway_phase = random.uniform(0, 2 * math.pi)

    def update(self):
        progress = min(1.0, self.age / max(1, self.life))
        drift = 1.0 - progress
        self.x += self.vx * drift + math.sin(self.age * 0.18 + self.sway_phase) * 0.10
        self.y += self.vy * drift + math.cos(self.age * 0.16 + self.sway_phase) * 0.08
        self.rotation += self.rotation_speed
        self.age += 1
        progress = min(1.0, self.age / max(1, self.life))
        self.opacity = max(0.0, (1.0 - progress) ** 1.35)
        self.scale = 0.72 + 0.28 * self.opacity

    def is_dead(self):
        return self.age > self.life or self.opacity <= 0.01

    @classmethod
    def _emoji_image(cls, size):
        font_size = max(12, int(round(size * 1.35)))
        cached = cls._emoji_cache.get(font_size)
        if cached is not None:
            return cached

        canvas = max(32, font_size * 3)
        image = QImage(canvas, canvas, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(0)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setFont(QFont("Segoe UI Emoji", font_size))
        painter.drawText(QRectF(0, 0, canvas, canvas), Qt.AlignmentFlag.AlignCenter, "🌸")
        painter.end()

        min_x, min_y = canvas, canvas
        max_x, max_y = -1, -1
        for y in range(canvas):
            for x in range(canvas):
                if image.pixelColor(x, y).alpha() > 0:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

        if max_x >= min_x and max_y >= min_y:
            padding = max(2, font_size // 10)
            crop = QRect(
                max(0, min_x - padding),
                max(0, min_y - padding),
                min(canvas - max(0, min_x - padding), max_x - min_x + 1 + padding * 2),
                min(canvas - max(0, min_y - padding), max_y - min_y + 1 + padding * 2),
            )
            image = image.copy(crop)

        cls._emoji_cache[font_size] = image
        return image

    def draw(self, painter, global_alpha=255, trail_scale=1.0):
        alpha = max(0, min(255, int(global_alpha * self.opacity)))
        if alpha <= 0:
            return

        trail_scale = max(0.25, min(1.0, float(trail_scale)))
        painter.save()
        painter.translate(self.x, self.y)
        painter.rotate(math.degrees(self.rotation))
        painter.scale(self.scale * trail_scale, self.scale * trail_scale)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setOpacity(alpha / 255.0)

        image = self._emoji_image(self.size)
        target_size = self.size * 1.45
        painter.drawImage(
            QRectF(-target_size / 2, -target_size / 2, target_size, target_size),
            image,
            QRectF(0, 0, image.width(), image.height()),
        )
        painter.restore()

class CursorTrailWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.translations = {}
        self.load_translations()        
        self.current_language = "ru"
        self.load_settings()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowState(Qt.WindowState.WindowFullScreen)

        self.trail = deque(maxlen=self.trail_length)
        self._last_cursor_pos = None
        self._settle_frames_remaining = 0
        self._last_sakura_spawn_pos = None
        self._sync_render_cache()
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self._render_tick)
        self.render_timer.start(16)

        # --- ТРЕЙ МЕНЮ С ПЕРЕВОДОМ ---
        style = QApplication.style()
        icon = style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
        else:
            icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
        app_icon = QIcon(icon_path)
        self.setWindowIcon(app_icon)
        self.tray_icon = QSystemTrayIcon(app_icon, self)
        self.tray_menu = QMenu()
        # Светлый стиль для меню трея
        self.tray_menu.setStyleSheet("""
            QMenu {
                background: #f5f5f5;
                color: #232323;
                border: 0px solid #bdbdbd;
            }
            QMenu::item:selected {
                background: #e0e0e0;
                color: #232323;
            }
        """)
        self.update_tray_menu()
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        self.rgb_phase = 0.0
        self.sakura_petals = []

    def open_themed_color_dialog(self, initial_color: QColor, parent=None):
        dlg_parent = parent if parent is not None else self
        use_dark = _resolve_dark_theme(dlg_parent, getattr(self, 'dark_theme_enabled', False))
        dlg = ModernColorDialog(initial_color if isinstance(initial_color, QColor) else QColor(initial_color), dlg_parent, use_dark)
        if dlg.exec():
            return dlg.selected_color()
        return QColor()

    def load_translations(self):
        try:
            # Исправлено: используем sys._MEIPASS для PyInstaller
            if hasattr(sys, '_MEIPASS'):
                translations_path = os.path.join(sys._MEIPASS, 'localization.json')
            else:
                translations_path = os.path.join(os.path.dirname(__file__), 'localization.json')
            with open(translations_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except Exception as e:
            logger.exception('Failed to load translations from %s', translations_path)
            self.translations = {"ru": {}, "en": {}, "zh": {}, "ja": {}}

    def tr(self, key):
        return self.translations.get(self.current_language, {}).get(key, key)

    def _sync_render_cache(self):
        colors = self.gradient_colors if getattr(self, "gradient_colors", None) else ["#3399ff", "#ffffff"]
        self._gradient_qcolors = [QColor(color) for color in colors]
        self._gradient_segment_count = max(0, len(self._gradient_qcolors) - 1)

    def _rgb_color(self, t):
        r, g, b = colorsys.hsv_to_rgb((self.rgb_phase + t) % 1.0, 1.0, 1.0)
        return QColor(int(r * 255), int(g * 255), int(b * 255))

    def _gradient_color(self, t):
        colors = getattr(self, "_gradient_qcolors", None) or [QColor("#3399ff")]
        num_segments = len(colors) - 1
        if num_segments <= 0:
            return QColor(colors[0])

        seg = min(int(t * num_segments), num_segments - 1)
        local_t = (t - seg / num_segments) * num_segments
        c1 = colors[seg]
        c2 = colors[seg + 1]
        return QColor(
            int(c1.red() + (c2.red() - c1.red()) * local_t),
            int(c1.green() + (c2.green() - c1.green()) * local_t),
            int(c1.blue() + (c2.blue() - c1.blue()) * local_t),
        )

    def _add_sakura_petal(self, pos, base_size, max_petals):
        if max_petals <= 0:
            return
        while len(self.sakura_petals) >= max_petals:
            self.sakura_petals.pop(0)
        self.sakura_petals.append(SakuraPetal(pos, base_size))

    def _spawn_sakura_trail(self, previous_pos, current_pos, max_petals):
        if max_petals <= 0:
            self.sakura_petals.clear()
            self._last_sakura_spawn_pos = None
            return

        base_size = max(10.0, self.trail_width * 1.9)
        if previous_pos is None or self._last_sakura_spawn_pos is None:
            self._last_sakura_spawn_pos = QPointF(float(current_pos.x()), float(current_pos.y()))
            self._add_sakura_petal(current_pos, base_size, max_petals)
            return

        spacing = max(5.0, min(14.0, self.trail_width * 0.95))
        start = QPointF(self._last_sakura_spawn_pos)
        end = QPointF(float(current_pos.x()), float(current_pos.y()))
        spawned = 0

        while spawned < 6:
            dx = end.x() - start.x()
            dy = end.y() - start.y()
            distance = math.hypot(dx, dy)
            if distance < spacing:
                break

            ratio = spacing / distance
            start = QPointF(start.x() + dx * ratio, start.y() + dy * ratio)
            jitter = max(1.2, self.trail_width * 0.22)
            petal_pos = QPointF(
                start.x() + random.uniform(-jitter, jitter),
                start.y() + random.uniform(-jitter, jitter),
            )
            self._add_sakura_petal(petal_pos, base_size, max_petals)
            spawned += 1

        self._last_sakura_spawn_pos = start

    def _render_tick(self):
        pos = QCursor.pos()
        previous_pos = self._last_cursor_pos
        moved = previous_pos is None or pos != previous_pos
        needs_repaint = False

        if moved:
            self.trail.appendleft(pos)
            self._last_cursor_pos = QPoint(pos)
            self._settle_frames_remaining = max(0, int(self.trail_length))
            needs_repaint = True
        elif self.trail and self._settle_frames_remaining > 0:
            self.trail.appendleft(pos)
            self._settle_frames_remaining -= 1
            needs_repaint = True

        if getattr(self, "rgb_trail_enabled", False) and len(self.trail) >= 2:
            self.rgb_phase = (self.rgb_phase + 0.02) % 1.0
            needs_repaint = True

        if self.sakura_trail_enabled:
            max_petals = max(12, int(self.trail_length) * 2)
            if moved or self._last_sakura_spawn_pos is not None:
                self._spawn_sakura_trail(previous_pos, pos, max_petals)
            if self.sakura_petals:
                for petal in self.sakura_petals:
                    petal.update()
                self.sakura_petals = [p for p in self.sakura_petals if not p.is_dead()][:max_petals]
                needs_repaint = True
        elif self.sakura_petals:
            self.sakura_petals.clear()
            self._last_sakura_spawn_pos = None
            needs_repaint = True

        if needs_repaint:
            self.update()

    def update_rgb_phase(self):
        self._render_tick()

    def update_sakura(self):
        self._render_tick()

    def load_settings(self):
        settings_path = get_settings_path()
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.trail_length = data.get('trail_length', 30)
                self.trail_width = data.get('trail_width', 8)
                self.gradient_colors = data.get('gradient_colors', ["#3399ff", "#ffffff"])
                self.fade_enabled = data.get('fade_enabled', True)
                self.alpha = data.get('alpha', 255)
                self.glow_enabled = data.get('glow_enabled', False)
                self.glow_color = data.get('glow_color', "#00ffff")
                self.outline_enabled = data.get('outline_enabled', False)
                self.outline_color = data.get('outline_color', "#000000")
                self.rgb_trail_enabled = data.get('rgb_trail_enabled', False)
                self.sakura_trail_enabled = data.get('sakura_trail_enabled', False)
                self.pixel_trail_enabled = data.get('pixel_trail_enabled', False)
                self.current_language = data.get('language', 'ru')
                self.dark_theme_enabled = data.get('dark_theme_enabled', False)  # добавлено
                # load profiles dict if present
                self._profiles = data.get('profiles', {})
                # last selected profile (profiles are autosaved by default)
                self.selected_profile = data.get('selected_profile', None)
                # If no profiles exist, create a default 'Стандартный' profile and persist
                try:
                    if not self._profiles:
                        default_name = "Стандартный" if self.current_language == 'ru' else self.tr('profiles')
                        self._profiles = {default_name: [
                            self.trail_length, self.trail_width, self.gradient_colors,
                            self.fade_enabled, self.alpha, self.glow_enabled, self.glow_color,
                            self.outline_enabled, self.outline_color, self.rgb_trail_enabled,
                            self.sakura_trail_enabled, self.current_language, self.pixel_trail_enabled,
                            self.dark_theme_enabled
                        ]}
                        self.selected_profile = default_name
                        # persist default profile into settings.json
                        try:
                            self.save_settings()
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                logger.exception('Failed to load settings from %s', settings_path)
                self.set_default_settings()
        else:
            self.set_default_settings()

    def set_default_settings(self):
        self.trail_length = 30
        self.trail_width = 8
        self.gradient_colors = ["#3399ff", "#ffffff"]
        self.fade_enabled = True
        self.alpha = 255
        self.glow_enabled = False
        self.glow_color = "#00ffff"
        self.outline_enabled = False
        self.outline_color = "#000000"
        self.rgb_trail_enabled = False
        self.sakura_trail_enabled = False
        self.pixel_trail_enabled = False
        self.current_language = "ru"
        self.dark_theme_enabled = False  # добавлено

    def save_settings(self):
        settings_path = get_settings_path()
        data = {
            'trail_length': self.trail_length,
            'trail_width': self.trail_width,
            'gradient_colors': self.gradient_colors,
            'fade_enabled': self.fade_enabled,
            'alpha': self.alpha,
            'glow_enabled': self.glow_enabled,
            'glow_color': self.glow_color,
            'outline_enabled': self.outline_enabled,
            'outline_color': self.outline_color,
            'rgb_trail_enabled': self.rgb_trail_enabled,
            'sakura_trail_enabled': self.sakura_trail_enabled,
            'pixel_trail_enabled': self.pixel_trail_enabled,
            'language': self.current_language,
            'dark_theme_enabled': self.dark_theme_enabled  # добавлено
        }
        # include profiles if present
        if hasattr(self, '_profiles'):
            data['profiles'] = self._profiles
        # include selected profile (profiles are autosaved by default)
        try:
            data['selected_profile'] = getattr(self, 'selected_profile', None)
        except Exception:
            data['selected_profile'] = None
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            logger.exception('Failed to save settings to %s', settings_path)

    def update_tray_menu(self):
        self.tray_menu.clear()
        settings_action = self.tray_menu.addAction(self.tr("settings") + "...")
        settings_action.triggered.connect(self.open_settings)
        exit_action = self.tray_menu.addAction(self.tr("exit"))
        exit_action.triggered.connect(self.exit_app)
        # Автозапуск
        autostart_action = self.tray_menu.addAction(self.tr("autostart"))
        autostart_action.setCheckable(True)
        autostart_action.setChecked(self.is_autostart_enabled())
        autostart_action.triggered.connect(self.toggle_autostart)

    def open_settings(self):
        # If a settings dialog is already open, raise and activate it instead of creating a new one
        existing = getattr(self, '_settings_dialog', None)
        if existing is not None and existing.isVisible():
            try:
                existing.raise_()
                existing.activateWindow()
            except Exception:
                pass
            return

        dlg = SettingsDialog(
            self,
            self.trail_length,
            self.trail_width,
            self.gradient_colors,
            self.fade_enabled,
            self.alpha,
            self.glow_enabled,
            self.glow_color,
            self.outline_enabled,
            self.outline_color,
            self.rgb_trail_enabled,
            self.sakura_trail_enabled,
            self.current_language,
            getattr(self, "pixel_trail_enabled", False),
            getattr(self, "dark_theme_enabled", False)  # передаем новое значение
        )

        # keep reference so subsequent calls reuse same dialog
        self._settings_dialog = dlg

        def _clear_settings_dialog():
            if getattr(self, '_settings_dialog', None) is dlg:
                self._settings_dialog = None

        try:
            dlg.finished.connect(lambda _=None: _clear_settings_dialog())
        except Exception:
            pass

        def apply_from_dialog(settings):
            (
                new_trail_length, new_trail_width, new_gradient_colors,
                new_fade_enabled, new_alpha, new_glow_enabled, new_glow_color,
                new_outline_enabled, new_outline_color, new_rgb_trail_enabled,
                new_sakura_trail_enabled, new_language, new_pixel_trail_enabled,
                new_dark_theme_enabled
            ) = settings
            language_changed = (self.current_language != new_language)
            theme_changed = (self.dark_theme_enabled != new_dark_theme_enabled)
            self.trail_length = new_trail_length
            self.trail_width = new_trail_width
            self.gradient_colors = new_gradient_colors
            self.fade_enabled = new_fade_enabled
            self.alpha = new_alpha
            self.glow_enabled = new_glow_enabled
            self.glow_color = new_glow_color
            self.outline_enabled = new_outline_enabled
            self.outline_color = new_outline_color
            self.rgb_trail_enabled = new_rgb_trail_enabled
            self.sakura_trail_enabled = new_sakura_trail_enabled
            self.pixel_trail_enabled = new_pixel_trail_enabled
            self.current_language = new_language
            self.dark_theme_enabled = new_dark_theme_enabled
            old_trail = list(self.trail)
            self.trail = deque(old_trail, maxlen=self.trail_length)
            self._settle_frames_remaining = min(
                getattr(self, "_settle_frames_remaining", 0),
                int(self.trail_length)
            )
            self._sync_render_cache()
            self.save_settings()
            self.update_tray_menu()
            self.update()
            if language_changed:
                try:
                    dlg.update_language(self.translations, self.current_language)
                except Exception:
                    pass
            # Тёмная тема применяется только к окну настроек, поэтому вызов apply_theme здесь не нужен

        dlg.settingsApplied.connect(apply_from_dialog)
        try:
            dlg.exec()
        finally:
            _clear_settings_dialog()

    def update_language(self):
        # Обновить меню трея и перерисовать окно
        self.update_tray_menu()
        self.repaint()
        # Можно добавить дополнительные действия, если появятся другие надписи вне меню

    def updateTrail(self):
        self._render_tick()

    def paintEvent(self, event):
        # --- Sakura трейл ---
        if self.sakura_trail_enabled:
            if not self.sakura_petals:
                return
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            denominator = max(1, len(self.sakura_petals) - 1)
            for index, petal in enumerate(self.sakura_petals):
                position = index / denominator
                trail_scale = 0.38 + 0.62 * (position ** 0.85)
                petal.draw(painter, self.alpha, trail_scale)
            return

        points = list(self.trail)

        # --- Pixel трейл ---
        if getattr(self, "pixel_trail_enabled", False):
            if len(points) < 2:
                return
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            n = len(points)
            min_size = max(2, int(self.trail_width * 0.7))
            max_size = max(3, int(self.trail_width * 1.5))
            use_rgb = getattr(self, "rgb_trail_enabled", False)
            denominator = max(1, n - 1)
            for i, pos in enumerate(points):
                t = i / denominator
                c = self._rgb_color(t) if use_rgb else self._gradient_color(t)
                if self.fade_enabled:
                    seg_alpha = int(self.alpha * (1 - t) ** 1.5)
                else:
                    seg_alpha = self.alpha
                c.setAlpha(seg_alpha)
                size = int(max_size * (1-t) + min_size)
                # Glow (свечение)
                if self.glow_enabled:
                    glow_color = QColor(self.glow_color)
                    glow_color.setAlpha(int(seg_alpha * 0.25))
                    for factor in [2.5, 1.5]:
                        s = int(size * factor)
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(glow_color)
                        painter.drawRect(pos.x() - s//2, pos.y() - s//2, s, s)
                # Outline
                if self.outline_enabled:
                    outline_color = QColor(self.outline_color)
                    outline_color.setAlpha(seg_alpha)
                    s = size + 4
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(outline_color)
                    painter.drawRect(pos.x() - s//2, pos.y() - s//2, s, s)
                # Основной пиксель
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(c)
                painter.drawRect(pos.x() - size//2, pos.y() - size//2, size, size)
            return

        # ...обычный трейл...
        if len(points) < 2:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        n = len(points)
        denominator = max(1, n - 1)
        # --- Градиент по всем цветам или RGB трейл ---
        use_rgb = getattr(self, "rgb_trail_enabled", False)
        if use_rgb:
            # --- Outline (под трейлом) ---
            if self.outline_enabled:
                for i in range(n-1):
                    t = i / denominator
                    width = (self.trail_width + 4) * (1-t) + 2
                    outline_color = QColor(self.outline_color)
                    outline_color.setAlpha(self.alpha)
                    pen = QPen(outline_color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                    painter.setPen(pen)
                    painter.drawLine(points[i], points[i+1])
            # --- Glow (свечение) для RGB трейла ---
            for i in range(n-1):
                t = i / denominator
                base_color = self._rgb_color(t)
                width = self.trail_width * (1-t) + 2
                if self.glow_enabled:
                    for glow_pass, factor in enumerate([4.0, 2.5, 1.5]):
                        glow_c = QColor(base_color)
                        glow_c.setAlpha(int(self.alpha * (0.12 if glow_pass==0 else 0.18 if glow_pass==1 else 0.25)))
                        pen = QPen(glow_c, width * factor, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                        painter.setPen(pen)
                        painter.drawLine(points[i], points[i+1])
            # --- Основная линия ---
            for i in range(n-1):
                t = i / denominator
                c = self._rgb_color(t)
                if self.fade_enabled:
                    seg_alpha = int(self.alpha * (1 - t) ** 1.5)
                else:
                    seg_alpha = self.alpha
                c.setAlpha(seg_alpha)
                width = self.trail_width * (1-t) + 2
                pen = QPen(c, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(points[i], points[i+1])
            return  # Не рисуем обычный градиент

        # --- Glow (свечение) ---
        if self.glow_enabled:
            for glow_pass, factor in enumerate([4.0, 2.5, 1.5]):
                glow_color = QColor(self.glow_color)
                glow_color.setAlpha(int(self.alpha * (0.12 if glow_pass==0 else 0.18 if glow_pass==1 else 0.25)))
                for i in range(n-1):
                    t = i / denominator
                    width = self.trail_width * factor * (1-t) + 2
                    pen = QPen(glow_color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                    painter.setPen(pen)
                    painter.drawLine(points[i], points[i+1])
        # --- Outline ---
        if self.outline_enabled:
            outline_color = QColor(self.outline_color)
            outline_color.setAlpha(self.alpha)
            for i in range(n-1):
                t = i / denominator
                width = (self.trail_width + 4) * (1-t) + 2
                pen = QPen(outline_color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(points[i], points[i+1])
        # --- Основная линия с острым концом и градиентом по всем цветам ---
        for i in range(n-1):
            t = i / denominator
            c = self._gradient_color(t)
            if self.fade_enabled:
                seg_alpha = int(self.alpha * (1 - t) ** 1.5)
            else:
                seg_alpha = self.alpha
            c.setAlpha(seg_alpha)
            width = self.trail_width * (1-t) + 2
            pen = QPen(c, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(points[i], points[i+1])

    def set_fade_enabled(self, enabled: bool):
        """Включает или отключает плавное затухание трейла на конце."""
        self.fade_enabled = enabled
        self.update()

    def closeEvent(self, event):
        self.save_settings()
        self.tray_icon.hide()
        event.accept()

    def exit_app(self):
        QApplication.quit()

    def get_autostart_shortcut_path(self):
        startup = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
        exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
        shortcut_path = os.path.join(startup, "CursorTrail.lnk")
        return shortcut_path, exe_path

    def enable_autostart(self):
        shortcut_path, exe_path = self.get_autostart_shortcut_path()
        ps_script = (
            f"$WshShell = New-Object -ComObject WScript.Shell;"
            f"$Shortcut = $WshShell.CreateShortcut('{shortcut_path}');"
            f"$Shortcut.TargetPath = '{exe_path}';"
            f"$Shortcut.WorkingDirectory = '{os.path.dirname(exe_path)}';"
            f"$Shortcut.IconLocation = '{exe_path}';"
            f"$Shortcut.Save();"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True, text=True,
            creationflags=CREATE_NO_WINDOW
        )
        if result.returncode != 0:
            print("Ошибка автозапуска:", result.stderr)
        return result.returncode == 0

    def disable_autostart(self):
        shortcut_path, _ = self.get_autostart_shortcut_path()
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)

    def is_autostart_enabled(self):
        shortcut_path, exe_path = self.get_autostart_shortcut_path()
        return os.path.exists(shortcut_path)

    def toggle_autostart(self, checked):
        if checked:
            self.enable_autostart()
        else:
            self.disable_autostart()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = CursorTrailWidget()
    w.show()
    sys.exit(app.exec())

import sys, os, json, random, math, colorsys, subprocess
import logging
from PySide6.QtWidgets import (
    QApplication, QWidget, QStackedWidget, QSlider, QColorDialog, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QDialog, QCheckBox, QFrame, QGridLayout, QSystemTrayIcon, QMenu, QStyle, QListWidget, QListWidgetItem, QAbstractItemView, QScrollArea, QComboBox, QSizePolicy, QInputDialog
)
from PySide6.QtCore import Qt, QTimer, QPoint, QRect, QPointF, QSize, QRectF, QUrl, QPropertyAnimation, QEasingCurve, Signal, Property, Slot
from PySide6.QtGui import QPainter, QColor, QPen, QCursor, QIcon, QPainterPath, QFont, QSurfaceFormat, QLinearGradient, QPixmap
from collections import deque
from PySide6.QtQuickWidgets import QQuickWidget


def themed_get_color(initial, parent=None, dark=False):
    dlg = QColorDialog(parent)
    dlg.setCurrentColor(initial if isinstance(initial, QColor) else QColor(initial))
    # try to use theme-provided stylesheet functions
    try:
        if dark:
            from dark_theme import get_color_dialog_stylesheet
        else:
            from light_theme import get_color_dialog_stylesheet
        css = get_color_dialog_stylesheet()
        if css:
            dlg.setStyleSheet(css)
    except Exception:
        # fallback simple style
        if dark:
            dlg.setStyleSheet("QWidget { background: #2b2b2b; color: #fff; } QPushButton { background: #3a3a3a; color: #fff; }")
        else:
            dlg.setStyleSheet("QWidget { background: #f5f5f5; color: #232323; } QPushButton { background: #ffffff; color: #232323; }")
    if dlg.exec():
        return dlg.selectedColor()
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
    """Simple two-button toggle widget.

    Signals:
        valueChanged(bool): emitted when toggle state changes.
    """
    valueChanged = Signal(bool)
    def set_dark_theme(self, enabled):
        if enabled:
            from dark_theme import (
                toggle_active_left_style, toggle_active_right_style,
                toggle_inactive_left_style, toggle_inactive_right_style
            )
            active_left = toggle_active_left_style()
            active_right = toggle_active_right_style()
            inactive_left = toggle_inactive_left_style()
            inactive_right = toggle_inactive_right_style()
        else:
            from light_theme import (
                toggle_active_left_style, toggle_active_right_style,
                toggle_inactive_left_style, toggle_inactive_right_style
            )
            active_left = toggle_active_left_style()
            active_right = toggle_active_right_style()
            inactive_left = toggle_inactive_left_style()
            inactive_right = toggle_inactive_right_style()
        # Применяем отдельные стили для левой (Off) и правой (On) кнопок
        if self.value:
            # On активен
            self.on_btn.setStyleSheet(active_right)
            self.off_btn.setStyleSheet(inactive_left)
        else:
            # Off активен
            self.off_btn.setStyleSheet(active_left)
            self.on_btn.setStyleSheet(inactive_right)
    def __init__(self, value=True, parent=None):
        super().__init__(parent)
        self.value = value
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Делаем кнопки On/Off больше и заметнее
        self.off_btn = QPushButton("Off")
        self.on_btn = QPushButton("On")
        for btn in [self.off_btn, self.on_btn]:
            btn.setFixedSize(64, 40)
            f = QFont("Segoe UI", 11)
            f.setBold(True)
            btn.setFont(f)
        self.off_btn.clicked.connect(lambda: self.setValue(False))
        self.on_btn.clicked.connect(lambda: self.setValue(True))
        layout.addWidget(self.off_btn)
        layout.addWidget(self.on_btn)
        self.setValue(value)

    def setValue(self, value):
        old = getattr(self, '_value', None)
        self.value = value
        # Автоматически применять текущую тему
        parent = self.parent()
        dark = False
        # Поиск по иерархии родителей, если есть dark_theme_enabled
        while parent is not None:
            if hasattr(parent, 'dark_theme_enabled'):
                dark = getattr(parent, 'dark_theme_enabled')
                break
            parent = getattr(parent, 'parent', lambda: None)()
        self.set_dark_theme(dark)

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

class ColorSliderWidget(QWidget):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
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
                painter.setPen(QColor("#232323"))
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
            pen = QPen(QColor("#232323"))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(knob_rect.adjusted(0,0,0,0), 6, 6)
            # Выделение (закруглённая обводка вокруг маркера)
            if i == self.selected:
                sel_rect = knob_rect.adjusted(-3, -3, 3, 3)
                painter.setPen(QPen(QColor("#232323"), 2))
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
    def set_dark_theme(self, enabled):
        if enabled:
            btn_style = """
                QPushButton {
                    background: #232323;
                    color: #fff;
                    font: bold 18pt 'Segoe UI';
                    border-radius: 8px;
                }
                QPushButton:hover { background: #2a2a2a; }
            """
        else:
            btn_style = """
                QPushButton {
                    background: #f5f5f5;
                    color: #232323;
                    font: bold 18pt 'Segoe UI';
                    border-radius: 8px;
                    border: 0px solid #bdbdbd;
                }
                QPushButton:hover { background: #e0e0e0; }
                QPushButton:pressed { background: #d6d6d6; }
            """
        self.minus_btn.setStyleSheet(btn_style)
        self.plus_btn.setStyleSheet(btn_style)
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.colors = list(colors) if colors else ["#3399ff", "#ffffff"]
        self.setMinimumHeight(56)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.minus_btn = QPushButton("-")
        self.minus_btn.setFixedSize(36, 36)
        self.minus_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                color: #232323;
                font: bold 18pt 'Segoe UI';
                border-radius: 8px;
                border: 0px solid #bdbdbd;
            }
            QPushButton:hover { background: #e0e0e0; }
            QPushButton:pressed { background: #d6d6d6; }
        """)
        self.minus_btn.clicked.connect(self.remove_color)
        layout.addWidget(self.minus_btn)
        self.slider = GradientSliderWidget(self.colors)
        self.slider.onOrderChanged = self.on_colors_changed
        layout.addWidget(self.slider, 1)
        self.plus_btn = QPushButton("+")
        self.plus_btn.setFixedSize(36, 36)
        self.plus_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                color: #232323;
                font: bold 18pt 'Segoe UI';
                border-radius: 8px;
                border: 0px solid #bdbdbd;
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

    def add_color(self):
        color = themed_get_color(QColor("#ffffff"), self, getattr(self, 'dark_theme_enabled', False))
        if color.isValid():
            insert_pos = self.slider.selected + 1
            self.colors.insert(insert_pos, color.name())
            self.slider.selected = insert_pos
            self.slider.set_colors(self.colors)
            self.slider.update()

    def remove_color(self):
        if len(self.colors) > 2:
            idx = self.slider.selected
            self.colors.pop(idx)
            self.slider.selected = max(0, idx-1)
            self.slider.set_colors(self.colors)
            self.slider.update()

    def get_colors(self):
        return self.slider.get_colors()

    def set_colors(self, colors):
        try:
            self.colors = list(colors)
            self.slider.set_colors(self.colors)
            self.slider.update()
        except Exception:
            logger.exception('Failed to set colors for ColorGradientPicker')

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
        self.setFixedSize(820, 680)
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
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Боковое меню ---
        self.menu_widget = QWidget()
        self.menu_widget.setFixedWidth(180)
        if self.dark_theme_enabled:
            DarkThemeMixin.apply_menu_style(self, self.menu_widget)
        else:
            LightThemeMixin.apply_menu_style(self, self.menu_widget)
        menu_layout = QVBoxLayout(self.menu_widget)
        menu_layout.setContentsMargins(0, 44, 0, 44)
        menu_layout.setSpacing(8)
        self.tab_buttons = []
        self.tabs = [self.tr("line"), self.tr("effects"), self.tr("profiles"), self.tr("settings_tab")]
        for i, name in enumerate(self.tabs):
            btn = QPushButton(name)
            btn.setFixedHeight(48)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setStyleSheet(self._tab_btn_style(selected=(i==0)))
            btn.clicked.connect(lambda checked, idx=i: self.select_tab(idx))
            menu_layout.addWidget(btn)
            self.tab_buttons.append(btn)
        menu_layout.addStretch()
        main_layout.addWidget(self.menu_widget)

        # --- Стек вкладок ---
        self.stacked = QStackedWidget()
        main_layout.addWidget(self.stacked, 1)

        # --- Вкладка 1: Линия (все существующие элементы) ---
        line_tab = QWidget()
        line_layout = QVBoxLayout(line_tab)
        line_layout.setContentsMargins(44, 44, 44, 44)
        line_layout.setSpacing(24)
        grid = QGridLayout()
        grid.setHorizontalSpacing(32)
        grid.setVerticalSpacing(28)
        label_width = 220  # Фиксированная ширина для всех лейблов

        lbl_trail_length = QLabel(self.tr("trail_length"))
        lbl_trail_length.setFixedWidth(label_width)
        grid.addWidget(lbl_trail_length, 0, 0)
        self.length_slider = QSlider(Qt.Orientation.Horizontal)
        self.length_slider.setMinimum(5)
        self.length_slider.setMaximum(100)
        self.length_slider.setValue(trail_length)
        self.length_slider.setStyleSheet("QSlider::handle:horizontal { background-color: #f5f5f5; width: 20px; margin: -6px 0; }")
        grid.addWidget(self.length_slider, 0, 1)

        lbl_trail_width = QLabel(self.tr("trail_width"))
        lbl_trail_width.setFixedWidth(label_width)
        grid.addWidget(lbl_trail_width, 1, 0)
        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setMinimum(1)
        self.width_slider.setMaximum(40)
        self.width_slider.setValue(trail_width)
        self.width_slider.setStyleSheet("QSlider::handle:horizontal { background-color: #f5f5f5; width: 20px; margin: -6px 0; }")
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
        self.alpha_slider.setStyleSheet("QSlider::handle:horizontal { background-color: #f5f5f5; width: 20px; margin: -6px 0; }")
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
        glow_border = '#444' if getattr(self, 'dark_theme_enabled', False) else '#bdbdbd'
        self.glow_color_btn.setStyleSheet(f"background: {glow_color}; border: 1px solid {glow_border}; border-radius: 6px;")
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
        outline_border = '#444' if getattr(self, 'dark_theme_enabled', False) else '#bdbdbd'
        self.outline_color_btn.setStyleSheet(f"background: {outline_color}; border: 1px solid {outline_border}; border-radius: 6px;")
        outline_layout.addWidget(self.outline_switch)
        outline_layout.addSpacing(8)
        outline_layout.addWidget(self.outline_color_btn)
        outline_layout.addStretch()
        outline_widget = QWidget()
        outline_widget.setLayout(outline_layout)
        grid.addWidget(outline_widget, 6, 1)
        line_layout.addLayout(grid)
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
        effects_layout.setContentsMargins(44, 44, 44, 44)
        effects_layout.setSpacing(24)
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
        rgb_widget.setLayout(rgb_layout)
        # --- fix: выставляем отступы и spacing для rgb_layout сразу ---
        rgb_layout.setContentsMargins(0, 0, 0, 0)
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
        sakura_widget.setLayout(sakura_layout)
        # --- fix: выставляем отступы и spacing для sakura_layout сразу ---
        sakura_layout.setContentsMargins(0, 0, 0, 0)
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
        pixel_widget.setLayout(pixel_layout)
        # --- fix: выставляем отступы и spacing для pixel_layout сразу ---
        pixel_layout.setContentsMargins(0, 0, 0, 0)
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
        profiles_layout.setContentsMargins(44, 44, 44, 44)
        profiles_layout.setSpacing(12)

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
        settings_layout.setContentsMargins(44, 44, 44, 44)
        settings_layout.setSpacing(24)
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
        self.version_label = QLabel("Version: 1.1", settings_tab)
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
        # Кнопки "Применить"
        # Кнопки "Применить" теперь стилизуются только через apply_theme миксинов
        # ComboBox (языки)
        # Стилизация lang_combo теперь только через apply_theme миксинов

        # --- Кнопка закрытия ---
        if not hasattr(self, 'close_btn'):
            self.close_btn = QPushButton("✕", self)
            self.close_btn.setFixedSize(36, 36)
            self.close_btn.move(self.width() - 44, 8)
            self.close_btn.clicked.connect(self.close)
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
            self.gear_label.move(8, 8)
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

    # --- Profiles methods (moved inside SettingsDialog) ---
    def list_profiles(self):
        return list(getattr(self, '_profiles', {}).keys())

    def save_profile(self):
        # Use a themed QInputDialog so its appearance matches the current theme
        try:
            dlg = QInputDialog(self)
            dlg.setWindowTitle(self.tr('save_profile'))
            dlg.setLabelText(self.tr('profile_name'))
            dlg.setTextValue("")
            try:
                # Apply a strict light stylesheet: white background, white buttons with 1px border, black text
                css = """
                    QWidget { background: #ffffff; color: #000000; }
                    QDialog { background: #ffffff; }
                    QLabel { color: #000000; }
                    QLineEdit { background: #ffffff; color: #000000; border: 1px solid #e0e0e0; padding: 6px; }
                    QPushButton { background: #ffffff; color: #000000; border: 1px solid #cfcfcf; border-radius: 6px; padding: 6px 10px; }
                    QPushButton:hover { background: #f5f5f5; }
                    QPushButton:pressed { background: #e9e9e9; }
                """
                dlg.setStyleSheet(css)
            except Exception:
                pass
            res = dlg.exec()
            name = dlg.textValue() if res == QDialog.Accepted else None
            if not name:
                return
        except Exception:
            # fallback to simple static call
            name, ok = QInputDialog.getText(self, self.tr('save_profile'), self.tr('profile_name'))
            if not ok or not name:
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
        glow_border = '#444' if getattr(self, 'dark_theme_enabled', False) else '#bdbdbd'
        self.glow_color_btn.setStyleSheet(f"background: {self.glow_color}; border: 1px solid {glow_border}; border-radius: 6px;")
        try:
            self.outline_switch.setValue(new_outline_enabled)
        except Exception:
            try:
                self.outline_switch.value = new_outline_enabled
            except Exception:
                pass
        self.outline_color = new_outline_color
        outline_border = '#444' if getattr(self, 'dark_theme_enabled', False) else '#bdbdbd'
        self.outline_color_btn.setStyleSheet(f"background: {self.outline_color}; border: 1px solid {outline_border}; border-radius: 6px;")
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
        if hasattr(self.parent(), 'save_settings'):
            self.parent().dark_theme_enabled = self.dark_theme_enabled
            self.parent().save_settings()
        # --- Обновить стиль version_label при смене темы ---
        self._update_version_label_style()
        # --- Кнопка закрытия ---
        if not hasattr(self, 'close_btn'):
            self.close_btn = QPushButton("✕", self)
            self.close_btn.setFixedSize(36, 36)
            self.close_btn.move(self.width() - 44, 8)
            self.close_btn.clicked.connect(self.close)
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
            self.gear_label.move(8, 8)
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

    def select_tab(self, idx):
        # Update tab button states/styles
        for i, btn in enumerate(self.tab_buttons):
            btn.setChecked(i == idx)
            btn.setStyleSheet(self._tab_btn_style(selected=(i==idx)))

        # Cross-fade between current and target page
        current_idx = self.stacked.currentIndex()
        if current_idx == idx:
            return

        current_widget = self.stacked.widget(current_idx)
        next_widget = self.stacked.widget(idx)

        # Ensure widgets are positioned correctly for animation
        # place both widgets to occupy the stacked widget area so child layouts keep correct positions
        try:
            w = self.stacked.width()
            h = self.stacked.height()
            current_widget.setGeometry(0, 0, w, h)
            next_widget.setGeometry(0, 0, w, h)
        except Exception:
            pass
        # make sure the next widget is visible for the fade-in (it will be made current after animation)
        next_widget.setVisible(True)

        # Prepare opacity effects
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        from PySide6.QtCore import QPropertyAnimation

        # Cancel any running animations
        if hasattr(self, '_tab_anim_current') and getattr(self, '_tab_anim_current') is not None:
            try:
                self._tab_anim_current.stop()
            except Exception:
                pass
        if hasattr(self, '_tab_anim_next') and getattr(self, '_tab_anim_next') is not None:
            try:
                self._tab_anim_next.stop()
            except Exception:
                pass

        current_effect = QGraphicsOpacityEffect(current_widget)
        current_widget.setGraphicsEffect(current_effect)
        next_effect = QGraphicsOpacityEffect(next_widget)
        next_widget.setGraphicsEffect(next_effect)

        current_anim = QPropertyAnimation(current_effect, b"opacity", self)
        current_anim.setDuration(180)
        current_anim.setStartValue(1.0)
        current_anim.setEndValue(0.0)
        current_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        next_anim = QPropertyAnimation(next_effect, b"opacity", self)
        next_anim.setDuration(180)
        next_anim.setStartValue(0.0)
        next_anim.setEndValue(1.0)
        next_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self._tab_anim_current = current_anim
        self._tab_anim_next = next_anim

        def on_finished():
            try:
                # finalize: set the target page and clear effects
                self.stacked.setCurrentIndex(idx)
                # ensure stacked-managed geometry restored
                try:
                    current_widget.setGeometry(0, 0, self.stacked.width(), self.stacked.height())
                    next_widget.setGeometry(0, 0, self.stacked.width(), self.stacked.height())
                except Exception:
                    pass
                current_widget.setGraphicsEffect(None)
                next_widget.setGraphicsEffect(None)
            finally:
                self._tab_anim_current = None
                self._tab_anim_next = None
                self._update_tab_labels_style()

        # Connect finish on next_anim to finalize (so page has finished appearing)
        next_anim.finished.connect(on_finished)

        # Start animations
        current_anim.start()
        next_anim.start()

    def _update_tab_labels_style(self):
        label_color = "#fff" if self.dark_theme_enabled else "#232323"
        font = "font: bold 16pt 'Segoe UI';"
        # Вкладка 1
        grid = self.stacked.widget(0).layout().itemAt(0).layout()
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
                profiles_lbl.setStyleSheet(f"color: {label_color}; font: bold 18pt 'Segoe UI';")
        except Exception:
            pass

    def _move_version_label(self):
        # Перемещаем версию в правый нижний угол вкладки "Настройки" (ещё ниже, чем подпись автора)
        settings_tab = self.stacked.widget(3)
        if hasattr(self, 'version_label') and self.version_label.parent() is settings_tab:
            w = settings_tab.width()
            h = settings_tab.height()
            label_w = self.version_label.width()
            label_h = self.version_label.height()
            margin = 12
            # Сдвигаем ещё ниже (например, +10px от нижнего края окна)
            self.version_label.move(w - label_w - margin, h - label_h - margin + 200)

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
            self.author_label.move(12, self.height() - self.author_label.height() - 12)
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
            glow_border = '#444' if getattr(self, 'dark_theme_enabled', False) else '#bdbdbd'
            self.glow_color_btn.setStyleSheet(f"background: {self.glow_color}; border: 1px solid {glow_border}; border-radius: 6px;")

    def choose_outline_color(self):
        color = themed_get_color(QColor(self.outline_color), self, getattr(self, 'dark_theme_enabled', False))
        if color.isValid():
            self.outline_color = color.name()
            outline_border = '#444' if getattr(self, 'dark_theme_enabled', False) else '#bdbdbd'
            self.outline_color_btn.setStyleSheet(f"background: {self.outline_color}; border: 1px solid {outline_border}; border-radius: 6px;")

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
            btn.setText(self.tabs[i])
            btn.setStyleSheet(self._tab_btn_style(selected=(i == self.stacked.currentIndex())))
        # Обновить все подписи и кнопки
        # Вкладка 1
        grid = self.stacked.widget(0).layout().itemAt(0).layout()
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
            rgb_widget.layout().setContentsMargins(0, 0, 0, 0)
            rgb_widget.layout().setSpacing(32)
        # Sakura трейл
        sakura_widget = effects_layout.itemAt(1).widget()
        if sakura_widget is not None and isinstance(sakura_widget.layout(), QHBoxLayout):
            sakura_widget.layout().setContentsMargins(0, 0, 0, 0)
            sakura_widget.layout().setSpacing(32)
        # Pixel трейл
        pixel_widget = effects_layout.itemAt(2).widget()
        if pixel_widget is not None and isinstance(pixel_widget.layout(), QHBoxLayout):
            pixel_widget.layout().setContentsMargins(0, 0, 0, 0)
            pixel_widget.layout().setSpacing(32)

class SakuraPetal:
    def __init__(self, pos, base_size):  # Добавляем параметр base_size
        self.x, self.y = pos.x(), pos.y()
        self.size = random.uniform(base_size * 0.8, base_size * 1.2)  # Используем base_size
        self.vx = random.uniform(-0.7, 0.7)
        self.vy = random.uniform(1.2, 2.2)
        self.rotation = random.uniform(0, 2*math.pi)
        self.rotation_speed = random.uniform(-0.03, 0.03)
        self.life = random.randint(60, 120)
        self.age = 0
        self.opacity = 1.0  # Для плавного исчезновения

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rotation += self.rotation_speed
        self.age += 1
        # Плавное исчезновение
        fade_start = int(self.life * 0.6)  # Начинаем исчезать после 60% времени жизни
        if self.age > fade_start:
            self.opacity = max(0.0, 1.0 - (self.age - fade_start) / (self.life - fade_start))

    def is_dead(self):
        return self.age > self.life or self.opacity <= 0.01

    def draw(self, painter):
        painter.save()
        painter.translate(self.x, self.y)
        painter.rotate(math.degrees(self.rotation))
        # Устанавливаем прозрачность
        painter.setOpacity(self.opacity)
        # Рисуем эмодзи вместо кастомной формы
        font = QFont("Segoe UI Emoji", int(self.size))
        painter.setFont(font)
        painter.drawText(QPointF(-self.size/2, self.size/2), "🌸")
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
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTrail)
        self.timer.start(16)  # ~60 FPS

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

        self.rgb_phase = 0.0  # Для анимации RGB трейла
        self.rgb_timer = QTimer(self)
        self.rgb_timer.timeout.connect(self.update_rgb_phase)
        self.rgb_timer.start(30)  # ~33 FPS для плавности

        self.sakura_trail_enabled = self.sakura_trail_enabled  # Используем значение из load_settings
        self.sakura_petals = []
        self.sakura_timer = QTimer(self)
        self.sakura_timer.timeout.connect(self.update_sakura)
        self.sakura_timer.start(16)

    def open_themed_color_dialog(self, initial_color: QColor, parent=None):
        """Open QColorDialog themed according to current app theme and return QColor."""
        dlg_parent = parent if parent is not None else self
        dlg = QColorDialog(dlg_parent)
        dlg.setCurrentColor(initial_color if isinstance(initial_color, QColor) else QColor(initial_color))
        # Apply minimal themed stylesheet so dialog matches app theme
        if getattr(self, 'dark_theme_enabled', False):
            dlg.setStyleSheet("QWidget { background: #2b2b2b; color: #fff; } QButton { background: #3a3a3a; color: #fff; }")
        else:
            dlg.setStyleSheet("QWidget { background: #f5f5f5; color: #232323; } QButton { background: #ffffff; color: #232323; }")
        if dlg.exec():
            return dlg.selectedColor()
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

    def update_rgb_phase(self):
        if getattr(self, "rgb_trail_enabled", False):
            self.rgb_phase = (self.rgb_phase + 0.02) % 1.0
            self.update()

    def update_sakura(self):
        if self.sakura_trail_enabled:  # Используем напрямую без getattr
            # Настройка "Длина следа" влияет на максимальное количество лепестков
            max_petals = self.trail_length
            
            # Добавляем новые лепестки, если их меньше чем trail_length
            overlay = getattr(self, '_qml_overlay', None)
            if overlay is not None:
                root = overlay.rootObject()
                if root is not None and hasattr(root, 'spawnPetal'):
                    # Спавним лепесток в QML
                    if random.random() < 0.35:
                        pos = QCursor.pos()
                        color = self.gradient_colors[0] if self.gradient_colors else '#ffb3b3'
                        try:
                            local = overlay.mapFromGlobal(pos)
                            root.spawnPetal(local.x(), local.y(), float(self.trail_width) * 2.0, color)
                        except Exception:
                            try:
                                root.spawnPetal(pos.x(), pos.y(), float(self.trail_width) * 2.0, color)
                            except Exception:
                                pass
            else:
                if len(self.sakura_petals) < max_petals and random.random() < 0.35:
                    pos = QCursor.pos()
                    # Настройка "Толщина следа" влияет на размер лепестков
                    self.sakura_petals.append(SakuraPetal(pos, self.trail_width * 2))
            
            # Обновляем и удаляем старые лепестки, оставляя не более max_petals
            # если используем QML — обновление лепестков делается в QML таймере
            if overlay is None:
                for petal in self.sakura_petals:
                    petal.update()
                self.sakura_petals = [p for p in self.sakura_petals if not p.is_dead()][:max_petals]
                self.update()
        else:
            if self.sakura_petals:
                self.sakura_petals.clear()
                self.update()

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

    def disable_legacy_renderer(self):
        # Останавливаем таймеры и очищаем списки, используемые старым рендерером
        try:
            if hasattr(self, 'timer') and self.timer is not None:
                self.timer.stop()
        except Exception:
            logger.exception('Error stopping main timer')
        try:
            if hasattr(self, 'rgb_timer') and self.rgb_timer is not None:
                self.rgb_timer.stop()
        except Exception:
            logger.exception('Error stopping rgb timer')
        try:
            if hasattr(self, 'sakura_timer') and self.sakura_timer is not None:
                self.sakura_timer.stop()
        except Exception:
            logger.exception('Error stopping sakura timer')
        # Очистить буферы
        if hasattr(self, 'trail'):
            self.trail.clear()
        if hasattr(self, 'sakura_petals'):
            self.sakura_petals.clear()
        # Устанавливаем флаг, чтобы paintEvent игнорировал старую отрисовку
        self._use_qml_trail = True

    def attach_qml_overlay(self, overlay):
        # Сохраняем ссылку на overlay и синхронизируем начальные настройки
        self._qml_overlay = overlay
        # счётчик попыток привязки (чтобы дождаться загрузки QML)
        if not hasattr(self, '_overlay_attach_attempts'):
            self._overlay_attach_attempts = {}
        self._overlay_attach_attempts[id(overlay)] = self._overlay_attach_attempts.get(id(overlay), 0) + 1
        attempt = self._overlay_attach_attempts.get(id(overlay), 1)
        if attempt > 12:
            # если слишком много попыток — отдаемся
            print('attach_qml_overlay: QML root not available after retries')
            return
        try:
            # maxPoints <- trail_length
            root = overlay.rootObject()
            if root is None:
                # QML ещё не загрузился — попробуем позже
                QTimer.singleShot(120, lambda: self.attach_qml_overlay(overlay))
                return
            if root is not None:
                if hasattr(root, 'setMaxPoints'):
                    root.setMaxPoints(int(self.trail_length))
                if hasattr(root, 'setBaseSize'):
                    root.setBaseSize(float(self.trail_width))
                # Вычислим базовый цвет: если RGB включён — используем first gradient color
                color = self.gradient_colors[0] if self.gradient_colors else '#ff5555'
                if hasattr(root, 'setTrailColor'):
                    root.setTrailColor(color)
                # Alpha: normalize 0..1
                a = max(0, min(1.0, (self.alpha or 255) / 255.0))
                if hasattr(root, 'setAlpha'):
                    root.setAlpha(a)
                # Gradient array
                if hasattr(root, 'setGradientColors'):
                    root.setGradientColors(self.gradient_colors)
                if hasattr(root, 'setFadeEnabled'):
                    root.setFadeEnabled(bool(self.fade_enabled))
                if hasattr(root, 'setRgbEnabled'):
                    root.setRgbEnabled(bool(self.rgb_trail_enabled))
                if hasattr(root, 'setGlowEnabled'):
                    root.setGlowEnabled(bool(self.glow_enabled))
                if hasattr(root, 'setGlowColor'):
                    root.setGlowColor(self.glow_color)
                if hasattr(root, 'setOutlineEnabled'):
                    root.setOutlineEnabled(bool(self.outline_enabled))
                if hasattr(root, 'setOutlineColor'):
                    root.setOutlineColor(self.outline_color)
                if hasattr(root, 'setSakuraEnabled'):
                    root.setSakuraEnabled(bool(self.sakura_trail_enabled))
                if hasattr(root, 'setPixelEnabled'):
                    root.setPixelEnabled(bool(self.pixel_trail_enabled))
                # тест-спавн убран — лепестки будут спавниться при движении курсора
        except Exception:
            logger.exception('attach_qml_overlay error')

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
            self.save_settings()
            self.update_tray_menu()
            self.update()
            # Если QML оверлей подключён — синхронизируем параметры
            try:
                overlay = getattr(self, '_qml_overlay', None)
                if overlay is not None:
                    root = overlay.rootObject()
                    if root is not None:
                        if hasattr(root, 'setMaxPoints'):
                            root.setMaxPoints(int(self.trail_length))
                        if hasattr(root, 'setBaseSize'):
                            root.setBaseSize(float(self.trail_width))
                        color = self.gradient_colors[0] if self.gradient_colors else '#ff5555'
                        if hasattr(root, 'setTrailColor'):
                            root.setTrailColor(color)
                        a = max(0, min(1.0, (self.alpha or 255) / 255.0))
                        if hasattr(root, 'setAlpha'):
                            root.setAlpha(a)
                        # дополнительные эффекты
                        if hasattr(root, 'setGradientColors'):
                            root.setGradientColors(self.gradient_colors)
                        if hasattr(root, 'setFadeEnabled'):
                            root.setFadeEnabled(bool(self.fade_enabled))
                        if hasattr(root, 'setRgbEnabled'):
                            root.setRgbEnabled(bool(self.rgb_trail_enabled))
                        if hasattr(root, 'setGlowEnabled'):
                            root.setGlowEnabled(bool(self.glow_enabled))
                        if hasattr(root, 'setGlowColor'):
                            root.setGlowColor(self.glow_color)
                        if hasattr(root, 'setOutlineEnabled'):
                            root.setOutlineEnabled(bool(self.outline_enabled))
                        if hasattr(root, 'setOutlineColor'):
                            root.setOutlineColor(self.outline_color)
                        if hasattr(root, 'setSakuraEnabled'):
                            root.setSakuraEnabled(bool(self.sakura_trail_enabled))
                        if hasattr(root, 'setPixelEnabled'):
                            root.setPixelEnabled(bool(self.pixel_trail_enabled))
                        if hasattr(root, 'clearPoints'):
                            root.clearPoints()
            except Exception as e:
                print('apply_from_dialog overlay sync error:', e)
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
        pos = QCursor.pos()
        self.trail.appendleft(pos)
        self.update()

    def paintEvent(self, event):
        # Если включён QML оверлей — не рисуем старый трейл
        if getattr(self, '_use_qml_trail', False):
            return
        # --- Sakura трейл ---
        if self.sakura_trail_enabled:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            for petal in self.sakura_petals:
                petal.draw(painter)
            return

        # --- Pixel трейл ---
        if getattr(self, "pixel_trail_enabled", False):
            if len(self.trail) < 2:
                return
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            n = len(self.trail)
            min_size = max(2, int(self.trail_width * 0.7))
            max_size = max(3, int(self.trail_width * 1.5))
            colors = [QColor(c) for c in self.gradient_colors]
            num_segments = len(colors) - 1
            for i in range(n):
                t = i / (n-1)
                # Цвет (обычный градиент или RGB)
                if getattr(self, "rgb_trail_enabled", False):
                    def hsv_to_rgb(h, s, v):
                        import colorsys
                        r, g, b = colorsys.hsv_to_rgb(h, s, v)
                        return int(r*255), int(g*255), int(b*255)
                    phase = (self.rgb_phase + t) % 1.0
                    r, g, b = hsv_to_rgb(phase, 1, 1)
                    c = QColor(r, g, b)
                else:
                    if num_segments == 0:
                        c = colors[0]
                    else:
                        seg = min(int(t * num_segments), num_segments - 1)
                        local_t = (t - seg / num_segments) * num_segments
                        c1 = colors[seg]
                        c2 = colors[seg+1]
                        r = int(c1.red() + (c2.red() - c1.red()) * local_t)
                        g = int(c1.green() + (c2.green() - c1.green()) * local_t)
                        b = int(c1.blue() + (c2.blue() - c1.blue()) * local_t)
                        c = QColor(r, g, b)
                if self.fade_enabled:
                    seg_alpha = int(self.alpha * (1 - t) ** 1.5)
                else:
                    seg_alpha = self.alpha
                c.setAlpha(seg_alpha)
                size = int(max_size * (1-t) + min_size)
                pos = self.trail[i]
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
        if len(self.trail) < 2:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        n = len(self.trail)
        path = QPainterPath()
        path.moveTo(self.trail[0])
        for pt in list(self.trail)[1:]:
            path.lineTo(pt)
        # --- Градиент по всем цветам или RGB трейл ---
        use_rgb = getattr(self, "rgb_trail_enabled", False)
        if use_rgb:
            # Генерируем динамический радужный градиент
            def hsv_to_rgb(h, s, v):
                import colorsys
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                return int(r*255), int(g*255), int(b*255)
            # --- Outline (под трейлом) ---
            if self.outline_enabled:
                for i in range(n-1):
                    t = i / (n-1)
                    width = (self.trail_width + 4) * (1-t) + 2
                    outline_color = QColor(self.outline_color)
                    outline_color.setAlpha(self.alpha)
                    pen = QPen(outline_color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                    painter.setPen(pen)
                    painter.drawLine(self.trail[i], self.trail[i+1])
            # --- Glow (свечение) для RGB трейла ---
            for i in range(n-1):
                t = i / (n-1)
                phase = (self.rgb_phase + t) % 1.0
                r, g, b = hsv_to_rgb(phase, 1, 1)
                width = self.trail_width * (1-t) + 2
                if self.glow_enabled:
                    for glow_pass, factor in enumerate([4.0, 2.5, 1.5]):
                        glow_c = QColor(r, g, b)
                        glow_c.setAlpha(int(self.alpha * (0.12 if glow_pass==0 else 0.18 if glow_pass==1 else 0.25)))
                        pen = QPen(glow_c, width * factor, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                        painter.setPen(pen)
                        painter.drawLine(self.trail[i], self.trail[i+1])
            # --- Основная линия ---
            for i in range(n-1):
                t = i / (n-1)
                phase = (self.rgb_phase + t) % 1.0
                r, g, b = hsv_to_rgb(phase, 1, 1)
                c = QColor(r, g, b)
                if self.fade_enabled:
                    seg_alpha = int(self.alpha * (1 - t) ** 1.5)
                else:
                    seg_alpha = self.alpha
                c.setAlpha(seg_alpha)
                width = self.trail_width * (1-t) + 2
                pen = QPen(c, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(self.trail[i], self.trail[i+1])
            return  # Не рисуем обычный градиент
        # --- Градиент по всем цветам ---
        colors = [QColor(c) for c in self.gradient_colors]
        num_segments = len(colors) - 1
        # --- Glow (свечение) ---
        if self.glow_enabled:
            for glow_pass, factor in enumerate([4.0, 2.5, 1.5]):
                glow_color = QColor(self.glow_color)
                glow_color.setAlpha(int(self.alpha * (0.12 if glow_pass==0 else 0.18 if glow_pass==1 else 0.25)))
                for i in range(n-1):
                    t = i / (n-1)
                    width = self.trail_width * factor * (1-t) + 2
                    pen = QPen(glow_color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                    painter.setPen(pen)
                    painter.drawLine(self.trail[i], self.trail[i+1])
        # --- Outline ---
        if self.outline_enabled:
            outline_color = QColor(self.outline_color)
            outline_color.setAlpha(self.alpha)
            for i in range(n-1):
                t = i / (n-1)
                width = (self.trail_width + 4) * (1-t) + 2
                pen = QPen(outline_color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(self.trail[i], self.trail[i+1])
        # --- Основная линия с острым концом и градиентом по всем цветам ---
        for i in range(n-1):
            t = i / (n-1)
            # Определяем, между какими цветами интерполировать
            if num_segments == 0:
                c = colors[0]
            else:
                seg = min(int(t * num_segments), num_segments - 1)
                local_t = (t - seg / num_segments) * num_segments
                c1 = colors[seg]
                c2 = colors[seg+1]
                r = int(c1.red() + (c2.red() - c1.red()) * local_t)
                g = int(c1.green() + (c2.green() - c1.green()) * local_t)
                b = int(c1.blue() + (c2.blue() - c1.blue()) * local_t)
                c = QColor(r, g, b)
            if self.fade_enabled:
                seg_alpha = int(self.alpha * (1 - t) ** 1.5)
            else:
                seg_alpha = self.alpha
            c.setAlpha(seg_alpha)
            width = self.trail_width * (1-t) + 2
            pen = QPen(c, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.trail[i], self.trail[i+1])

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

    # Улучшение формата рендеринга для QQuickWidget (GPU)
    fmt = QSurfaceFormat()
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)

    # Основной виджет приложения
    w = CursorTrailWidget()
    w.show()

    # QML оверлей с трейлом: transparent, не перехватывает мышь
    class QmlTrailOverlay(QQuickWidget):
        def __init__(self, qml_path, parent=None):
            super().__init__(parent)
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setClearColor(Qt.GlobalColor.transparent)
            self.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
            self.setSource(QUrl.fromLocalFile(os.path.abspath(qml_path)))
            # Показываем поверх всех окон, но без рамки
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)

        def push_point(self, x, y):
            root = self.rootObject()
            if root is not None and hasattr(root, 'pushPoint'):
                root.pushPoint(x, y)

        def set_trail_color(self, color):
            root = self.rootObject()
            if root is not None and hasattr(root, 'setTrailColor'):
                root.setTrailColor(color)

    qml_path = os.path.join(os.path.dirname(__file__), 'trail.qml')
    if not os.path.exists(qml_path):
        logger.error('QML file not found: %s', qml_path)
        overlay = None
    else:
        try:
            overlay = QmlTrailOverlay(qml_path)
        except Exception:
            logger.exception('Failed to create QmlTrailOverlay for %s', qml_path)
            overlay = None
    if overlay is not None:
        overlay.setGeometry(0, 0, w.width(), w.height())
        overlay.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        overlay.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        overlay.show()

    # Отключаем старую рендер-логику и привязываем QML оверлей
    try:
        w.disable_legacy_renderer()
        if overlay is not None:
            w.attach_qml_overlay(overlay)
        else:
            logger.warning('Overlay not created; falling back to legacy renderer')
    except Exception:
        logger.exception('overlay attach error')

    # Обновление позиции курсора и передача в QML
    def update_overlay():
        pos = QCursor.pos()
        try:
            if overlay is None:
                raise RuntimeError("overlay not available")
            local = overlay.mapFromGlobal(pos)
            overlay.push_point(local.x(), local.y())
            # Спавним лепесток в QML, если включена сакура
            try:
                root = overlay.rootObject()
                if root is not None and getattr(w, 'sakura_trail_enabled', False):
                    if hasattr(root, 'spawnPetal'):
                        # розовый цвет для лепестков
                        root.spawnPetal(local.x(), local.y(), float(w.trail_width) * 2.0, '#ffb3b3')
            except Exception:
                logger.exception('Failed to spawn petal via QML (local coordinates)')
        except Exception:
            try:
                if overlay is not None:
                    overlay.push_point(pos.x(), pos.y())
                    root = overlay.rootObject()
                    if root is not None and getattr(w, 'sakura_trail_enabled', False):
                        if hasattr(root, 'spawnPetal'):
                            root.spawnPetal(pos.x(), pos.y(), float(w.trail_width) * 2.0, '#ffb3b3')
            except Exception:
                logger.exception('Failed to push point or spawn petal via QML (global coordinates)')

    timer = QTimer()
    timer.timeout.connect(update_overlay)
    timer.start(16)

    # Следим за изменением размера основного окна
    def on_main_resize(event=None):
        if overlay is not None:
            try:
                overlay.setGeometry(0, 0, w.width(), w.height())
            except Exception:
                logger.exception('Failed to resize overlay')

    # Подвешиваем обработчик размера
    old_resize = w.resizeEvent
    def new_resize(event):
        try:
            old_resize(event)
        except Exception:
            pass
        on_main_resize(event)
    w.resizeEvent = new_resize

    sys.exit(app.exec())
import sys, os, json, time, threading
from urllib.request import urlopen

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QGridLayout, QVBoxLayout,
    QHBoxLayout, QPushButton, QDialog, QLineEdit, QScrollArea,
    QFrame, QDoubleSpinBox
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QFont, QPixmap, QCursor,
    QMouseEvent, QBrush, QFontMetrics
)
from PyQt6.QtCore import (
    Qt, QTimer, QPoint, QRectF, pyqtSignal, QThread,
    QObject, pyqtSlot
)

BG_DEEP = QColor(8, 8, 8)
BG_BASE = QColor(12, 12, 12)
BG_PANEL = QColor(18, 18, 18)
BG_HOVER = QColor(26, 26, 26)
BG_TILE = QColor(14, 14, 14)
LINE_DIM = QColor(30, 30, 30)
LINE_MID = QColor(48, 48, 48)
LINE_BRIGHT = QColor(72, 72, 72)
TEXT_WHITE = QColor(240, 240, 240)
TEXT_MID = QColor(150, 150, 150)
TEXT_DIM = QColor(70, 70, 70)
TEXT_MUTED = QColor(45, 45, 45)
ACCENT = QColor(220, 220, 220)

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "invoker_config.json")
ICON_CDN = "https://courier.spectral.gg/images/dota/spellicons/"
ICONS_DIR = os.path.join(os.path.dirname(__file__), ".icons_cache")

SOCIAL_LINKS = {
    "github": "https://github.com/MakeHimCake",
    "telegram": "https://t.me/Sborpozor"
}

SPELLS = [
    {"name": "Cold Snap", "ru_name": "Cold Snap", "orbs": "QQQ", "key": "cold_snap"},
    {"name": "Ghost Walk", "ru_name": "Ghost Walk", "orbs": "QQW", "key": "ghost_walk"},
    {"name": "Ice Wall", "ru_name": "Ice Wall", "orbs": "QQE", "key": "ice_wall"},
    {"name": "Tornado", "ru_name": "Tornado", "orbs": "QWW", "key": "tornado"},
    {"name": "EMP", "ru_name": "EMP", "orbs": "WWW", "key": "emp"},
    {"name": "Alacrity", "ru_name": "Alacrity", "orbs": "WWE", "key": "alacrity"},
    {"name": "Deafening Blast", "ru_name": "Deafening Blast", "orbs": "QWE", "key": "deafening_blast"},
    {"name": "Forge Spirit", "ru_name": "Forge Spirit", "orbs": "QEE", "key": "forge_spirit"},
    {"name": "Chaos Meteor", "ru_name": "Chaos Meteor", "orbs": "WEE", "key": "chaos_meteor"},
    {"name": "Sun Strike", "ru_name": "Sun Strike", "orbs": "EEE", "key": "sun_strike"},
]

DEFAULT_CONFIG = {
    "key_q": "q", "key_w": "w", "key_e": "e", "key_invoke": "r",
    "delay": 0.05, "opacity": 0.96, "x": -1, "y": -1,
    "binds": {s["name"]: f"F{i+1}" for i, s in enumerate(SPELLS)},
    "icon_size": 36,
}

ORB_COLORS = {"Q": QColor(120, 200, 255), "W": QColor(120, 255, 180), "E": QColor(255, 180, 80)}

def _load_local_icon(name: str, size: int = 20) -> QPixmap:
    os.makedirs(ICONS_DIR, exist_ok=True)
    path = os.path.join(ICONS_DIR, f"{name}.png")
    if os.path.exists(path):
        pm = QPixmap(path)
        if not pm.isNull():
            return pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
    return QPixmap()

def load_icon_from_cdn(spell_key: str, size: int = 36) -> QPixmap:
    os.makedirs(ICONS_DIR, exist_ok=True)
    cache_path = os.path.join(ICONS_DIR, f"{spell_key}.png")
    if os.path.exists(cache_path):
        pm = QPixmap(cache_path)
        if not pm.isNull():
            return pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
    url = f"{ICON_CDN}{spell_key}.png"
    try:
        data = urlopen(url, timeout=5).read()
        with open(cache_path, "wb") as f:
            f.write(data)
        pm = QPixmap()
        pm.loadFromData(data)
        if not pm.isNull():
            return pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
    except Exception:
        pass
    return QPixmap()

class CastSignals(QObject):
    casted = pyqtSignal(str)

class Caster(QThread):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self._queue = []
        self._lock = threading.Lock()
        self.signals = CastSignals()
        self._run = True

    def enqueue(self, name: str):
        with self._lock:
            self._queue.append(name)

    def run(self):
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
        except ImportError:
            return
        while self._run:
            name = None
            with self._lock:
                if self._queue:
                    name = self._queue.pop(0)
            if name:
                spell = next((s for s in SPELLS if s["name"] == name), None)
                if spell:
                    d = float(self.config.get("delay", 0.05))
                    for orb in spell["orbs"]:
                        k = self.config.get(f"key_{orb.lower()}", orb.lower())
                        pyautogui.keyDown(k); time.sleep(0.02); pyautogui.keyUp(k)
                        time.sleep(d)
                    inv = self.config.get("key_invoke", "r")
                    pyautogui.keyDown(inv); time.sleep(0.02); pyautogui.keyUp(inv)
                    self.signals.casted.emit(name)
            time.sleep(0.008)

    def stop(self):
        self._run = False
        self.quit()

class OrbTag(QWidget):
    def __init__(self, letter: str, parent=None):
        super().__init__(parent)
        self.letter = letter
        self.setFixedSize(14, 14)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(LINE_MID))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, 14, 14, 2, 2)
        p.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        p.setPen(TEXT_MID)
        p.drawText(QRectF(0, 0, 14, 14), Qt.AlignmentFlag.AlignCenter, self.letter)
        p.end()

class SpellTile(QWidget):
    clicked = pyqtSignal(str)

    def __init__(self, spell: dict, bind: str, icon_size: int = 36, parent=None):
        super().__init__(parent)
        self.spell = spell
        self.bind = bind
        self.icon_size = icon_size
        self._hover = False
        self._active = False
        self._flash = 0.0
        self._pixmap = load_icon_from_cdn(spell["key"], icon_size)
        self._flash_timer = QTimer(self)
        self._flash_timer.timeout.connect(self._tick)
        self.setFixedSize(220, 46)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def flash(self):
        self._flash = 1.0
        self._active = True
        self._flash_timer.start(16)
        QTimer.singleShot(600, self._deactivate)

    def _deactivate(self):
        self._active = False
        self.update()

    def _tick(self):
        self._flash = max(0.0, self._flash - 0.05)
        self.update()
        if self._flash <= 0:
            self._flash_timer.stop()

    def enterEvent(self, e): self._hover = True; self.update()
    def leaveEvent(self, e): self._hover = False; self.update()
    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.spell["name"])

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        bg = BG_HOVER if self._hover else (QColor(30,30,30) if self._active else BG_TILE)
        border = LINE_MID if self._hover else (LINE_BRIGHT if self._active else LINE_DIM)
        p.setBrush(QBrush(bg))
        p.setPen(QPen(border, 1))
        p.drawRoundedRect(0, 0, w - 1, h - 1, 3, 3)
        if self._flash > 0:
            p.setBrush(QBrush(QColor(255, 255, 255, int(self._flash * 18))))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(0, 0, w - 1, h - 1, 3, 3)
        ix = 8
        if self._pixmap and not self._pixmap.isNull():
            p.setOpacity(0.75 if not self._hover else 1.0)
            p.drawPixmap(ix, (h - self.icon_size) // 2, self._pixmap)
            p.setOpacity(1.0)
        tx = ix + self.icon_size + 10
        p.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        name_color = TEXT_WHITE if self._hover or self._active else TEXT_MID
        p.setPen(name_color)
        p.drawText(QRectF(tx, 6, w - tx - 60, 16),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   self.spell["ru_name"])
        orb_x = tx
        for letter in self.spell["orbs"]:
            c = ORB_COLORS.get(letter, TEXT_DIM)
            c_dim = QColor(c.red(), c.green(), c.blue(), 90 if not self._hover else 160)
            p.setBrush(QBrush(c_dim))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(orb_x, 26, 12, 12, 2, 2)
            p.setFont(QFont("Consolas", 6, QFont.Weight.Bold))
            p.setPen(QColor(255, 255, 255, 160))
            p.drawText(QRectF(orb_x, 26, 12, 12), Qt.AlignmentFlag.AlignCenter, letter)
            orb_x += 15
        p.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        fm = QFontMetrics(p.font())
        bw = fm.horizontalAdvance(self.bind) + 10
        bx = w - bw - 6
        by = (h - 16) // 2
        bg_key = QColor(22, 22, 22) if not self._hover else QColor(35, 35, 35)
        p.setBrush(QBrush(bg_key))
        p.setPen(QPen(LINE_MID, 1))
        p.drawRoundedRect(bx, by, bw, 16, 2, 2)
        p.setPen(TEXT_MID if not self._hover else TEXT_WHITE)
        p.drawText(QRectF(bx, by, bw, 16), Qt.AlignmentFlag.AlignCenter, self.bind)
        p.end()

def make_sep():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet("background:#1e1e1e;border:none;")
    return f

class CastIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self._alpha = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._fade)
        self.setFixedHeight(20)

    def show_cast(self, text: str):
        self._text = text
        self._alpha = 220
        self._timer.start(50)
        self.update()

    def _fade(self):
        self._alpha = max(0, self._alpha - 12)
        self.update()
        if self._alpha <= 0:
            self._timer.stop()

    def paintEvent(self, _):
        if not self._text or self._alpha == 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(QFont("Consolas", 7))
        p.setPen(QColor(180, 180, 180, self._alpha))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"▸ {self._text}")
        p.end()

class SocialButton(QWidget):
    clicked = pyqtSignal()

    def __init__(self, name: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.url = SOCIAL_LINKS.get(icon_name, "")
        self._hover = False
        self._pixmap = _load_local_icon(icon_name, size=18)
        self.setFixedSize(170, 28)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def enterEvent(self, e): self._hover = True; self.update()
    def leaveEvent(self, e): self._hover = False; self.update()
    
    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton and self.url:
            import webbrowser
            webbrowser.open(self.url)
            self.clicked.emit()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        bg = BG_HOVER if self._hover else BG_TILE
        border = LINE_MID if self._hover else LINE_DIM
        p.setBrush(QBrush(bg))
        p.setPen(QPen(border, 1))
        p.drawRoundedRect(0, 0, w-1, h-1, 3, 3)
        ix = 8
        if self._pixmap and not self._pixmap.isNull():
            p.setOpacity(0.8 if not self._hover else 1.0)
            p.drawPixmap(ix, (h-18)//2, self._pixmap)
            p.setOpacity(1.0)
        p.setFont(QFont("Consolas", 7))
        p.setPen(TEXT_MID if not self._hover else TEXT_WHITE)
        p.drawText(QRectF(ix+22, 0, w-28, h), 
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                   self.name)
        p.end()

class Overlay(QWidget):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.caster = Caster(config)
        self.caster.signals.casted.connect(self._on_casted)
        self.caster.start()
        self._hotkeys = []
        self._tiles: dict[str, SpellTile] = {}
        self._drag_pos = None
        self._visible = True
        self._init_window()
        self._build_ui()
        self._register_hotkeys()
        if config["x"] >= 0 and config["y"] >= 0:
            self.move(config["x"], config["y"])
        else:
            scr = QApplication.primaryScreen().geometry()
            self.move(scr.width() - 250, scr.height() // 2 - 280)

    def _init_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setWindowOpacity(self.config.get("opacity", 0.96))

    def _build_ui(self):
        self.setFixedWidth(240)
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(0)
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 6)
        hdr.setSpacing(4)
        logo = QLabel("IESC")
        logo.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        logo.setStyleSheet("color:#ddd;background:transparent;letter-spacing:2px;")
        self._dot = QLabel("●")
        self._dot.setFont(QFont("Segoe UI", 6))
        self._dot.setStyleSheet("color:#555;background:transparent;")
        btn_s = self._icon_btn("≡", self._open_settings)
        btn_x = self._icon_btn("×", self._quit)
        hdr.addWidget(logo)
        hdr.addWidget(self._dot)
        hdr.addStretch()
        hdr.addWidget(btn_s)
        hdr.addWidget(btn_x)
        root.addLayout(hdr)
        root.addWidget(make_sep())
        root.addSpacing(6)
        orb_row = QHBoxLayout()
        orb_row.setContentsMargins(0, 0, 0, 6)
        orb_row.setSpacing(4)
        for orb, label in [("Q", "Quas"), ("W", "Wex"), ("E", "Exort")]:
            key = self.config.get(f"key_{orb.lower()}", orb.lower()).upper()
            tag = QLabel(f"{key} · {label}")
            tag.setFont(QFont("Consolas", 6))
            clr = ORB_COLORS[orb]
            tag.setStyleSheet(f"color:rgba({clr.red()},{clr.green()},{clr.blue()},160);background:transparent;")
            orb_row.addWidget(tag)
        orb_row.addStretch()
        root.addLayout(orb_row)
        icon_size = self.config.get("icon_size", 36)
        spells_layout = QVBoxLayout()
        spells_layout.setSpacing(2)
        for i, spell in enumerate(SPELLS):
            bind = self.config["binds"].get(spell["name"], f"F{i+1}")
            tile = SpellTile(spell, bind, icon_size, self)
            tile.clicked.connect(self._on_click)
            spells_layout.addWidget(tile)
            self._tiles[spell["name"]] = tile
        root.addLayout(spells_layout)
        root.addSpacing(6)
        root.addWidget(make_sep())
        root.addSpacing(4)
        self._cast_ind = CastIndicator(self)
        root.addWidget(self._cast_ind)

    def _icon_btn(self, text: str, cb):
        b = QPushButton(text)
        b.setFixedSize(20, 20)
        b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        b.setFont(QFont("Segoe UI", 10))
        b.setStyleSheet(
            "QPushButton{background:transparent;color:#444;border:none;}"
            "QPushButton:hover{color:#ccc;}"
        )
        b.clicked.connect(cb)
        return b

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setBrush(QBrush(BG_BASE))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, w, h, 6, 6)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(LINE_DIM, 1))
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 5.5, 5.5)
        p.end()

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e: QMouseEvent):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._drag_pos = None
        self.config["x"] = self.x()
        self.config["y"] = self.y()
        self._save_config()

    def _register_hotkeys(self):
        try:
            import keyboard as kb
        except ImportError:
            return
        for name, key in self.config["binds"].items():
            if key and key not in ("", "—"):
                try:
                    hk = kb.add_hotkey(key.lower(), lambda n=name: self.caster.enqueue(n), suppress=False)
                    self._hotkeys.append(hk)
                except Exception as ex:
                    print(f"Bind error [{key}]: {ex}")

    def _unregister_hotkeys(self):
        try:
            import keyboard as kb
            for hk in self._hotkeys:
                try: kb.remove_hotkey(hk)
                except: pass
        except ImportError:
            pass
        self._hotkeys.clear()

    def _on_click(self, name: str):
        self.caster.enqueue(name)

    @pyqtSlot(str)
    def _on_casted(self, name: str):
        spell = next((s for s in SPELLS if s["name"] == name), None)
        if spell:
            self._cast_ind.show_cast(spell["ru_name"])
            t = self._tiles.get(name)
            if t:
                t.flash()

    def _open_settings(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec():
            self.config = dlg.result_config
            self._save_config()
            self._unregister_hotkeys()
            self.caster.config = self.config
            self.setWindowOpacity(self.config.get("opacity", 0.96))
            for name, tile in self._tiles.items():
                tile.bind = self.config["binds"].get(name, "—")
                tile.update()
            self._register_hotkeys()

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Config save error: {e}")

    def _quit(self):
        self._unregister_hotkeys()
        try:
            import keyboard as kb; kb.unhook_all()
        except ImportError:
            pass
        self.caster.stop()
        QApplication.quit()

DARK_STYLE = """
QDialog, QWidget { background: #0c0c0c; color: #aaa; }
QLabel { color: #777; background: transparent; }
QLineEdit, QDoubleSpinBox {
    background: #111; color: #ddd;
    border: 1px solid #222; border-radius: 2px;
    padding: 3px 6px; font-family: Consolas; font-size: 8pt;
}
QLineEdit:focus, QDoubleSpinBox:focus { border-color: #444; }
QPushButton {
    background: #111; color: #777;
    border: 1px solid #222; border-radius: 2px;
    padding: 4px 10px; font-family: Consolas; font-size: 8pt;
}
QPushButton:hover { background: #1a1a1a; color: #ccc; border-color: #333; }
QPushButton#save { color: #aaa; border-color: #333; }
QPushButton#save:hover { background: #1a1a1a; color: #eee; }
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { background: #0c0c0c; width: 4px; }
QScrollBar::handle:vertical { background: #222; border-radius: 2px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
"""

class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        import copy
        self.result_config = copy.deepcopy(config)
        self._fields: dict = {}
        self._drag_pos = None
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(DARK_STYLE)
        self.setFixedWidth(380)
        self._build_ui()

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e: QMouseEvent):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._drag_pos = None

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(12, 12, 12, 252)))
        p.setPen(QPen(QColor(30, 30, 30), 1))
        p.drawRoundedRect(0, 0, self.width(), self.height(), 4, 4)

    def _lbl(self, text: str, dim: bool = True):
        l = QLabel(text)
        l.setFont(QFont("Consolas", 7, QFont.Weight.Bold if not dim else QFont.Weight.Normal))
        l.setStyleSheet(f"color:{'#555' if dim else '#888'};background:transparent;letter-spacing:1px;")
        return l

    def _field(self, value, width: int = 55):
        e = QLineEdit(str(value))
        e.setFont(QFont("Consolas", 8))
        e.setFixedWidth(width)
        e.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return e

    def _build_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(12, 10, 12, 12)
        v.setSpacing(8)
        hh = QHBoxLayout()
        t = QLabel("НАСТРОЙКИ")
        t.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        t.setStyleSheet("color:#bbb;background:transparent;letter-spacing:2px;")
        xb = QPushButton("×")
        xb.setFixedSize(20, 20)
        xb.setStyleSheet(
            "QPushButton{background:transparent;color:#444;border:none;font-size:14px;}"
            "QPushButton:hover{color:#aaa;}"
        )
        xb.clicked.connect(self.reject)
        hh.addWidget(t); hh.addStretch(); hh.addWidget(xb)
        v.addLayout(hh)
        v.addWidget(make_sep())
        v.addWidget(self._lbl("КЛАВИШИ", False))
        kg = QGridLayout(); kg.setSpacing(6); kg.setContentsMargins(0, 0, 0, 0)
        for i, (n, k) in enumerate([("Quas", "key_q"), ("Wex", "key_w"), ("Exort", "key_e"), ("Invoke", "key_invoke")]):
            f = self._field(self.result_config.get(k, ""), 42)
            self._fields[k] = f
            kg.addWidget(self._lbl(n), i // 2, (i % 2) * 2)
            kg.addWidget(f, i // 2, (i % 2) * 2 + 1)
        v.addLayout(kg)
        pg = QHBoxLayout(); pg.setSpacing(12)
        ds = QDoubleSpinBox()
        ds.setRange(0.01, 0.3); ds.setSingleStep(0.005); ds.setDecimals(3)
        ds.setValue(self.result_config.get("delay", 0.05)); ds.setFixedWidth(72)
        self._fields["delay"] = ds
        os_ = QDoubleSpinBox()
        os_.setRange(0.3, 1.0); os_.setSingleStep(0.05); os_.setDecimals(2)
        os_.setValue(self.result_config.get("opacity", 0.96)); os_.setFixedWidth(60)
        self._fields["opacity"] = os_
        dl = QVBoxLayout(); dl.setSpacing(2)
        dl.addWidget(self._lbl("задержка"))
        dl.addWidget(ds)
        ol = QVBoxLayout(); ol.setSpacing(2)
        ol.addWidget(self._lbl("прозрачность"))
        ol.addWidget(os_)
        pg.addLayout(dl); pg.addLayout(ol); pg.addStretch()
        v.addLayout(pg)
        v.addWidget(make_sep())
        v.addWidget(self._lbl("ПРИВЯЗКИ", False))
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setMaximumHeight(180)
        sc.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        inn = QWidget(); inn.setStyleSheet("background:transparent;")
        bg = QGridLayout(inn); bg.setSpacing(4); bg.setContentsMargins(0, 0, 4, 0)
        for i, sp in enumerate(SPELLS):
            nl = QLabel(sp["ru_name"])
            nl.setFont(QFont("Consolas", 7))
            nl.setStyleSheet("color:#666;background:transparent;")
            bf = self._field(self.result_config["binds"].get(sp["name"], f"F{i+1}"), 52)
            self._fields[f"bind_{sp['name']}"] = bf
            bg.addWidget(nl, i, 0)
            bg.addWidget(bf, i, 1)
        sc.setWidget(inn)
        v.addWidget(sc)
        v.addWidget(make_sep())
        v.addWidget(self._lbl("СОЦСЕТИ", False))
        social_layout = QVBoxLayout()
        social_layout.setSpacing(4)
        self._social_btns = {}
        for name, icon in [("Github", "github"), ("Telegram", "telegram")]:
            btn = SocialButton(name, icon)
            self._social_btns[icon] = btn
            social_layout.addWidget(btn)
        v.addLayout(social_layout)
        sb = QPushButton("СОХРАНИТЬ")
        sb.setObjectName("save")
        sb.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        sb.setFixedHeight(28)
        sb.clicked.connect(self._save)
        v.addWidget(sb)

    def _save(self):
        for k, w in self._fields.items():
            if k.startswith("bind_"):
                self.result_config["binds"][k[5:]] = w.text().strip() or "—"
            elif k in ("delay", "opacity"):
                self.result_config[k] = w.value()
            else:
                val = w.text().strip()
                if val:
                    self.result_config[k] = val
        self.accept()

def load_config() -> dict:
    import copy
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                loaded = json.load(f)
            m = copy.deepcopy(DEFAULT_CONFIG)
            m.update({k: v for k, v in loaded.items() if k != "binds"})
            m["binds"] = {**DEFAULT_CONFIG["binds"], **loaded.get("binds", {})}
            return m
        except Exception as e:
            print(f"Config error: {e}")
    return copy.deepcopy(DEFAULT_CONFIG)

if __name__ == "__main__":
    for pkg, imp in [("PyQt6", "PyQt6.QtWidgets"), ("keyboard", "keyboard"), ("pyautogui", "pyautogui")]:
        try:
            __import__(imp)
        except ImportError:
            print(f"Missing: pip install {pkg}")
            sys.exit(1)
    cfg = load_config()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    app.setStyleSheet("QToolTip{background:#111;color:#ccc;border:1px solid #2a2a2a;font-family:Consolas;font-size:7pt;}")
    ov = Overlay(cfg)
    ov.show()
    print("IESC")
    print("  Спиздишь прогу и меня не укажешь я обижусь ;(")
    sys.exit(app.exec())
import ctypes
from ctypes import WinDLL, byref, cast
from ctypes.wintypes import MSG, RECT, LPRECT

from PyQt5.QtCore import QSize, QEvent
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QLabel, QVBoxLayout


class FramelessWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.dwmapi = WinDLL("dwmapi")
        self.user32 = ctypes.windll.user32
        self.add_shadow()
        self.border_size = 8
        self.caption_area = [0, -240, 0, 30]

    def add_shadow(self):
        hwnd = int(self.winId())
        margins = RECT(-1, -1, -1, -1)
        self.dwmapi.DwmExtendFrameIntoClientArea(hwnd, byref(margins))

    def changeEvent(self, e):
        if e.type() == QEvent.WindowStateChange:
            hwnd = int(self.winId())
            # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
            self.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x27)

    def nativeEvent(self, event_type, message):
        msg = MSG.from_address(int(message))
        if msg.message == 0x0084:  # WM_NCHITTEST
            x = msg.lParam & 0xFFFF
            y = (msg.lParam >> 16) & 0xFFFF
            rect = RECT()
            self.user32.GetWindowRect(msg.hWnd, byref(rect))
            if self.border_size > 0 and not self.isMaximized():
                s = self.border_size
                h = 1 if x <= rect.left + s else 2 if x >= rect.right - s else 0
                v = 1 if y <= rect.top + s else 2 if y >= rect.bottom - s else 0
                if h or v:
                    return True, 9 + v * 3 + h
            caption_area = self.caption_area
            for i in range(0, len(self.caption_area), 4):
                x1 = caption_area[i + 0] + (rect.right + 1 if caption_area[i + 0] < 0 else rect.left)
                x2 = caption_area[i + 1] + (rect.right + 1 if caption_area[i + 1] < 0 else rect.left)
                y1 = caption_area[i + 2] + (rect.bottom + 1 if caption_area[i + 2] < 0 else rect.top)
                y2 = caption_area[i + 3] + (rect.bottom + 1 if caption_area[i + 3] < 0 else rect.top)
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return True, 2

        elif msg.message == 0x0083:  # WM_NCCALCSIZE
            if msg.wParam:
                if self.isMaximized():
                    rect = cast(msg.lParam, LPRECT).contents
                    rect.top += 8
                    rect.left += 8
                    rect.right -= 8
                    rect.bottom -= 8
                return True, 0x0300
            else:
                return True, 0
        return super().nativeEvent(event_type, message)


class FramelessWindowDemo(FramelessWindow):
    def __init__(self):
        super().__init__()
        self.titlebar = QWidget(self)
        self.titlebar.setFixedHeight(30)
        self.titlebar.setStyleSheet("background-color: #333; color: white;")
        self.close_button = QPushButton(self)
        self.close_button.setText("X")
        self.close_button.clicked.connect(self.close)
        self.minimal_button = QPushButton(self)
        self.minimal_button.setText("-")
        self.minimal_button.clicked.connect(self.showMinimized)
        self.maximal_button = QPushButton(self)
        self.maximal_button.setText("[]")
        self.maximal_button.clicked.connect(self._toggle_maximize)
        self.title_label = QLabel(self)
        self.title_label.setText("Frameless PyQt5 Window")
        layout1 = QHBoxLayout(self.titlebar)
        layout1.setContentsMargins(0, 0, 0, 0)
        layout1.addSpacing(10)
        layout1.addWidget(self.title_label, 1)
        layout1.addWidget(self.minimal_button)
        layout1.addWidget(self.maximal_button)
        layout1.addWidget(self.close_button)
        self.client_area = QWidget(self)
        self.client_area.setStyleSheet("background:#222")
        layout2 = QVBoxLayout(self)
        layout2.setContentsMargins(0, 0, 0, 0)
        layout2.setSpacing(0)
        layout2.addWidget(self.titlebar)
        layout2.addWidget(self.client_area, 1)

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def sizeHint(self):
        return QSize(800, 600)


def main():
    app = QApplication([])
    window = FramelessWindowDemo()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()

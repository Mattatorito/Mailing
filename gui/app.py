from __future__ import annotations
import sys, asyncio
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop
from .theme import ThemeManager
from .main_window import MainWindow
from . import styles

def main():
    app = QApplication(sys.argv)
    theme_mgr = ThemeManager()
    # Принудительно устанавливаем темную тему
    theme_mgr.set_dark(True)
    styles.apply_palette(app, True)  # Всегда темная тема
    app.setStyleSheet(styles.QSS_BASE)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    win = MainWindow(theme_mgr)
    win.show()

    with loop:
        loop.run_forever()

if __name__ == "__main__":  # pragma: no cover
    main()

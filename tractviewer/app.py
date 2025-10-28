"""Small runner that launches the UI.

This module is intentionally minimal; the widgets and IO functions live in
`tractviewer.ui`, `tractviewer.io` and `tractviewer.utils`.
"""

import sys
from PyQt5 import QtWidgets
from .ui import MainWindow
from .io import load_mri


def main():
    app = QtWidgets.QApplication(sys.argv)
    # try to load MRI if available; otherwise start with no volume
    try:
        vol = load_mri()
    except Exception:
        vol = None
    win = MainWindow(volume=vol)
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

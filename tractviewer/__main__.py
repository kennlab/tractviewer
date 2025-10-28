"""Small runner that launches the UI.

This module is intentionally minimal; the widgets and IO functions live in
`tractviewer.ui`, `tractviewer.io` and `tractviewer.utils`.
"""

import sys
from PyQt5 import QtWidgets
from tractviewer.io import load_mri
from tractviewer.ui.main import MainWindow



def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    if len(sys.argv) > 1:
        path = sys.argv[1]
        win.load_mri(path)
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

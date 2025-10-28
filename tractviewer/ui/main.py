from pathlib import Path
import numpy as np
from PyQt5 import QtCore, QtWidgets

from tractviewer.io import load_mri, load_grid
from tractviewer.ui.grid import GridWidget
from tractviewer.ui.mri import MRIView

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, volume=None):
        super().__init__()
        self.setWindowTitle('Tract Viewer - Grid + MRI')
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QHBoxLayout(central)

        self.grid = GridWidget()
        layout.addWidget(self.grid, 1)

        right = QtWidgets.QWidget()
        rlay = QtWidgets.QVBoxLayout(right)
        self.mri = MRIView(volume)
        rlay.addWidget(self.mri, 1)

        controls = QtWidgets.QWidget()
        cl = QtWidgets.QHBoxLayout(controls)
        cl.addWidget(QtWidgets.QLabel('Brightness'))
        self.brightness_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.brightness_slider.setMinimum(0)
        self.brightness_slider.setMaximum(600)
        self.brightness_slider.setValue(100)
        cl.addWidget(self.brightness_slider)
        cl.addWidget(QtWidgets.QLabel('Contrast'))
        self.contrast_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.contrast_slider.setMinimum(1)
        self.contrast_slider.setMaximum(600)
        self.contrast_slider.setValue(200)
        cl.addWidget(self.contrast_slider)

        self.zero_spinner = QtWidgets.QSpinBox()
        self.zero_spinner.setMinimum(0)
        self.zero_spinner.setMaximum(512)
        self.zero_spinner.setValue(0)
        cl.addWidget(self.zero_spinner)
        rlay.addWidget(controls)

        layout.addWidget(right, 2)

        self.grid.update_coords(load_grid())

        self.grid.point_clicked.connect(self.on_point_clicked)
        self.brightness_slider.valueChanged.connect(self.on_brightness_changed)
        self.contrast_slider.valueChanged.connect(self.on_contrast_changed)
        self.zero_spinner.valueChanged.connect(lambda val: setattr(self.mri, 'zero', val) or self.mri.update())

        self.on_brightness_changed(self.brightness_slider.value())
        self.on_contrast_changed(self.contrast_slider.value())

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        open_mri_action = QtWidgets.QAction('Open MRI...', self)
        open_mri_action.triggered.connect(self.open_mri)
        file_menu.addAction(open_mri_action)
        open_grid_action = QtWidgets.QAction('Open Grid...', self)
        open_grid_action.triggered.connect(self.open_grid)
        file_menu.addAction(open_grid_action)

    def on_point_clicked(self, r, c):
        if self.mri.volume is None:
            return
        center = (261, 248)
        col = int(2*r + center[1])
        slice_idx = int(2*c + center[0])
        print(f"Point clicked at grid row {r}, col {c} -> MRI slice {slice_idx}, column {col}")
        # try:
        #     mr = int(np.clip(r, 0, self.grid_mapping.shape[0] - 1))
        #     mc = int(np.clip(c, 0, self.grid_mapping.shape[1] - 1))
        #     val = self.grid_mapping[mr, mc]
        #     slice_idx = int(np.clip(round(float(val[0])), 0, self.mri.volume.shape[0] - 1))
        #     col_val = float(val[1])
        #     img_w = self.mri.volume.shape[2]
        #     if col_val <= 0 or col_val >= img_w:
        #         col = int(np.clip(mc * img_w / self.grid.cols + img_w / (2 * self.grid.cols), 0, img_w - 1))
        #     else:
        #         col = int(np.clip(round(col_val), 0, img_w - 1))
        # except Exception:
        #     img_w = self.mri.volume.shape[2]
        #     col = int(c * img_w / self.grid.cols + img_w / (2 * self.grid.cols))
        self.mri.set_slice(slice_idx)
        self.mri.set_column(col)

    def on_brightness_changed(self, val):
        b = float(val)
        self.mri.set_brightness_contrast(b, self.mri.contrast)

    def on_contrast_changed(self, val):
        c = float(val)
        self.mri.set_brightness_contrast(self.mri.brightness, c)

    def open_mri(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open MRI', str(Path.home()), 'NIfTI Files (*.nii *.nii.gz);;All Files (*)')
        if not path:
            return
        try:
            vol = load_mri(path)
            self.mri.set_volume(vol)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'Failed to load MRI: {e}')
    
    def load_mri(self, path):
        try:
            vol = load_mri(path)
            self.mri.set_volume(vol)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'Failed to load MRI: {e}')

    def open_grid(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open Grid (tracts.npy)', str(Path.home()), 'NumPy files (*.npy);;All Files (*)')
        if not path:
            return
        self.grid.update_coords(load_grid(path))
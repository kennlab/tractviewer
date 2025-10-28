from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
from typing import Optional

class GridWidget(QtWidgets.QWidget):
    point_clicked = QtCore.pyqtSignal(float, float)
    def __init__(self, coords: Optional[np.ndarray]=None, rect=None, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        # enable mouse move events even when no button is pressed
        self.setMouseTracking(True)

        self.selected = None
        self.hovered = None
        self.view_matrix = None
        self.model_matrix = None

        self.coords = None
        if coords is not None:
            self.update_coords(coords, rect)

    def update_coords(self, coords: np.ndarray, rect=None):
        self.coords = coords
        if rect is None:
            rect = [np.min(coords[:,0]), np.min(coords[:,1]), np.max(coords[:,0]), np.max(coords[:,1])]
        # rect is l,b,r,t in voxel space
        # make an affine that converts this to 0,0 at top-left and scales to width,height
        model = np.eye(3)
        model[0, 0] = 1.0 / (rect[2] - rect[0])  # scale x
        model[1, 1] = 1.0 / (rect[3] - rect[1])  # scale y
        model[0, 2] = -rect[0] * model[0, 0]  # translate x
        model[1, 2] = -rect[1] * model[1, 1]  # translate y
        self.model_matrix = model

    def paintEvent(self, event):
        if self.coords is None or self.model_matrix is None or self.view_matrix is None:
            return
        painter = QtGui.QPainter(self)
        rect = self.rect()
        w = rect.width()
        h = rect.height()
        painter.fillRect(rect, QtGui.QColor('white'))
        coords = np.append(self.coords, np.ones((self.coords.shape[0], 1)), axis=1)
        mapped = self.view_matrix @ self.model_matrix @ coords.T
        mapped = mapped.T
        
        R = 4
        for idx in range(mapped.shape[0]):
            x, y = mapped[idx, :2]
            px = int(x)
            py = int(y)
            if idx == self.selected:
                color = QtGui.QColor('red')
            elif idx == self.hovered:
                color = QtGui.QColor('blue')
            else:
                color = QtGui.QColor('black')
            # painter.setPen(QtGui.QColor('black'))
            # draw a filled circle
            painter.setBrush(color)
            painter.drawEllipse(px - R, py - R, 2 * R, 2 * R)
    
    def resizeEvent(self, event):
        self.view_matrix = np.eye(3)
        rect = self.rect()
        w, h = rect.width(), rect.height()
        margin = 10
        grid_w = w - 2 * margin
        grid_h = h - 2 * margin
        self.view_matrix[0, 0] = grid_w
        self.view_matrix[1, 1] = -grid_h
        self.view_matrix[0, 2] = margin
        self.view_matrix[1, 2] = h - margin

    def mouseToWorld(self, event):
        pos = event.pos()
        x, y = pos.x(), pos.y()
        # invert the view and model matrices to get back to voxel space
        inv_view = np.linalg.inv(self.view_matrix)
        inv_model = np.linalg.inv(self.model_matrix)
        pt = np.array([x, y, 1.0])
        voxel_pt = inv_model @ inv_view @ pt
        return voxel_pt[:2]

    def getHit(self, event):
        voxel_pt = self.mouseToWorld(event)
        tol = .5
        self.coords - voxel_pt
        dists = np.linalg.norm(self.coords[:, :2] - voxel_pt, axis=1)
        idx = np.argmin(dists)
        if dists[idx] > tol:
            return None
        return idx

    def mousePressEvent(self, event):
        idx = self.getHit(event)
        self.selected = idx
        if idx is None:
            return
        r, c = self.coords[idx, 0].item(), self.coords[idx, 1].item()
        self.point_clicked.emit(r, c)
        self.update()

    def mouseMoveEvent(self, event):
        """Show a tooltip with the grid coordinates under the cursor."""

        idx = self.getHit(event)
        self.hovered = idx
        if idx is None:
            return
        r, c = self.coords[idx, 0].item(), self.coords[idx, 1].item()
        text = f"row: {r}, col: {c}"
        QtWidgets.QToolTip.showText(event.globalPos(), text, self)
        self.update()

    def leaveEvent(self, event):
        QtWidgets.QToolTip.hideText()
        super().leaveEvent(event)

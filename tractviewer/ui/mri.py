import numpy as np
from PyQt5 import QtGui, QtWidgets, QtCore
from tractviewer.utils import numpy_to_qimage


class MRIView(QtWidgets.QLabel):
    """MRI display with preserved aspect ratio and rectangle crop tool.

    Left-drag inside the image to draw a rectangular crop region. On mouse
    release the volume will be cropped across all slices to the selected
    rectangle (in image coordinates). The image maintains aspect ratio when
    drawn in the widget.
    """

    def __init__(self, volume: np.ndarray = None, parent=None):
        super().__init__(parent)
        self.volume = volume
        self.slice_index = 0
        self.column_x = None
        # brightness/contrast interpreted as center and width for clipping
        self.brightness = 50
        self.contrast = 50
        self.setMinimumSize(300, 300)
        self.zero = 0
        # we will do custom painting to enforce aspect ratio
        self._pixmap = None
        self._display_rect = QtCore.QRect()
        # crop rectangle drawing state
        self._crop_active = False
        self._crop_start = None
        self._crop_rect = None
        self.crop_indices = None
        # keep original volume for undo (reset)
        self._original_volume = None
        # accept keyboard focus so keyPressEvent works
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        # enable mouse tracking
        self.setMouseTracking(True)

    def set_volume(self, vol: np.ndarray):
        if vol is None:
            self.volume = None
            self._pixmap = None
            self.update()
            return
        if vol.ndim != 3:
            raise ValueError('volume must be 3D')
        self.volume = vol
        # store a copy as the original for possible reset
        try:
            self._original_volume = np.array(vol, copy=True)
        except Exception:
            self._original_volume = None
        self.slice_index = max(0, min(self.slice_index, vol.shape[0] - 1))
        self.update_image()

    def set_slice(self, idx: int):
        if self.volume is None:
            return
        self.slice_index = max(0, min(idx, self.volume.shape[0] - 1))
        self.update_image()

    def set_column(self, x: int):
        self.column_x = x
        self.update()

    def set_brightness_contrast(self, brightness: float, contrast: float):
        self.brightness = brightness
        self.contrast = contrast
        self.update_image()

    def update_image(self):
        """Convert current slice to a QPixmap (stored in self._pixmap) and repaint."""
        if self.volume is None:
            self._pixmap = None
            self.update()
            return
        img = self.volume[self.slice_index].astype(np.float32)
        out = np.clip(img, self.brightness - self.contrast / 2.0, self.brightness + self.contrast / 2.0)
        qimg = numpy_to_qimage(out)
        self._pixmap = QtGui.QPixmap.fromImage(qimg)
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent):
        painter = QtGui.QPainter(self)
        rect = self.rect()
        painter.fillRect(rect, QtGui.QColor('black'))
        if self._pixmap is None:
            painter.end()
            return
        # compute display rect that preserves aspect ratio and centers the image
        # pw = self._pixmap.width()
        # ph = self._pixmap.height()
        pw = self._pixmap.width()
        ph = self._pixmap.height()
        if self.crop_indices is not None:
            x0, x1, y0, y1 = self.crop_indices
            w = x1 - x0
            h = y1 - y0
        else:
            x0, y0 = 0, 0
            w, h = pw, ph
        rw = rect.width()
        rh = rect.height()
        # make a rect that fits the cropped area while preserving aspect ratio
        scale = min(rw / pw, rh / ph)
        zoom = min(pw/w, ph/h)
        dw = int(pw * scale * zoom)
        dh = int(ph * scale * zoom)
        dx = rect.x() + (rw - dw) // 2 - int(x0 / zoom / 2)
        dy = rect.y() + (rh - dh) // 2 - int(y0 / zoom / 2)

        self._display_rect = QtCore.QRect(dx, dy, dw, dh)
        painter.drawPixmap(self._display_rect, self._pixmap)

        # draw vertical column line (map column_x in image coords to widget coords)
        if self.column_x is not None and self._pixmap is not None:
            img_w = self._pixmap.width()
            # map column from image coords -> display coords
            x_img = int(np.clip(self.column_x, 0, img_w - 1))
            x_disp = self._display_rect.left() + int(x_img * (self._display_rect.width() / img_w))
            pen = QtGui.QPen(QtGui.QColor('red'))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(x_disp, self._display_rect.top(), x_disp, self._display_rect.bottom())

            # draw points at 1mm increments along the column, assuming 1 pixel = .5mm
            # for mm in range(0, ph // 2 + 1):
            #     y_img_top = int(np.clip((ph // 2) - mm * 2, 0, ph - 1))
            #     y_img_bottom = int(np.clip((ph // 2) + mm * 2, 0, ph - 1))
            #     y_disp_top = self._display_rect.top() + int(y_img_top * (self._display_rect.height() / ph))
            #     y_disp_bottom = self._display_rect.top() + int(y_img_bottom * (self._display_rect.height() / ph))
            #     painter.setBrush(QtGui.QColor('red'))
            #     painter.drawEllipse(x_disp - 3, y_disp_top - 3, 6, 6)
            #     if mm != 0:
            #         painter.drawEllipse(x_disp - 3, y_disp_bottom - 3, 6, 6)
            increments = np.arange(self.zero, ph, 2)
            for mm in increments:
                x = x_disp
                y = self._display_rect.top() + int(mm * self._display_rect.height() / ph)
                painter.setBrush(QtGui.QColor('red'))
                if (mm - self.zero) % 5:
                    R = 1
                else:
                    R = 5
                painter.drawEllipse(x - R, y - R, R*2, R*2)

        # draw crop rectangle overlay if active or exists
        if self._crop_rect is not None:
            pen = QtGui.QPen(QtGui.QColor(0, 255, 0, 200))
            pen.setWidth(2)
            painter.setPen(pen)
            brush = QtGui.QBrush(QtGui.QColor(0, 255, 0, 40))
            painter.setBrush(brush)
            painter.drawRect(self._crop_rect)

        painter.end()

    def _widget_to_image(self, pos: QtCore.QPoint) -> tuple[int, int] | None:
        """Map a QPoint in widget coordinates to image (x,y) coordinates.

        Returns (x_img, y_img) or None if outside the displayed image.
        """
        if self._pixmap is None or self._display_rect.isNull():
            return None
        if not self._display_rect.contains(pos):
            return None
        rx = pos.x() - self._display_rect.left()
        ry = pos.y() - self._display_rect.top()
        img_w = self._pixmap.width()
        img_h = self._pixmap.height()
        x_img = int(np.clip(round(rx * img_w / self._display_rect.width()), 0, img_w - 1))
        y_img = int(np.clip(round(ry * img_h / self._display_rect.height()), 0, img_h - 1))
        return x_img, y_img

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        # start crop rectangle on left button
        if event.button() == QtCore.Qt.LeftButton:
            # only start if inside image
            if self._display_rect.contains(event.pos()):
                self._crop_active = True
                self._crop_start = event.pos()
                self._crop_rect = QtCore.QRect(self._crop_start, self._crop_start)
                self.update()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self._crop_active and self._crop_start is not None:
            self._crop_rect = QtCore.QRect(self._crop_start, event.pos()).normalized()
            # clamp to display rect
            self._crop_rect = self._crop_rect.intersected(self._display_rect)
            self.update()
        else:
            # if near a mm increment on the column, show a tooltip with the mm - self.zero value
            pos = event.pos()
            img_coords = self._widget_to_image(pos)
            if img_coords is not None and self._pixmap is not None and self.column_x is not None:
                x_img, y_img = img_coords
                if abs(x_img - self.column_x) < 3:
                    mm = (y_img - self.zero) // 2
                    QtWidgets.QToolTip.showText(event.globalPos(), f"{mm} mm", self)
                else:
                    QtWidgets.QToolTip.hideText()


    def compute_crop_indices(self) -> tuple[int, int, int, int] | None:
        """Compute crop indices (x0, x1, y0, y1) in image coordinates from the current crop rectangle.

        Returns None if no valid crop rectangle is defined.
        """
        if self._crop_rect is None or self._pixmap is None or self._display_rect.isNull():
            return None
        # map crop rect corners from widget coords to image coords
        top_left = self._widget_to_image(self._crop_rect.topLeft())
        bottom_right = self._widget_to_image(self._crop_rect.bottomRight())
        if top_left is None or bottom_right is None:
            return None
        x0, y0 = top_left
        x1, y1 = bottom_right
        if x0 > x1:
            x0, x1 = x1, x0
        if y0 > y1:
            y0, y1 = y1, y0
        if x1-x0 < 5 or y1-y0 < 5:
            return None
        return x0, x1, y0, y1

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton and self._crop_active:
            self.crop_indices = self.compute_crop_indices()
            self._crop_active = False
            self._crop_rect = None
            self.update_image()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        """Press 'h' to reset crop (restore original volume if available)."""
        if event.key() == QtCore.Qt.Key_H:
            self.crop_indices = None
            self.update()
        else:
            super().keyPressEvent(event)


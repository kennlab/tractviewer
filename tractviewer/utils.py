from typing import Optional, Tuple
import numpy as np
from PyQt5 import QtGui


def numpy_to_qimage(gray: np.ndarray, vlim: Optional[Tuple[int, int]]=None) -> QtGui.QImage:
    """Convert a 2D numpy array to a QImage (RGB32 grayscale).

    Note: simple implementation; can be optimized if needed.
    """
    if gray.ndim != 2:
        raise ValueError("numpy_to_qimage expects a 2D array")
    arr = gray.copy()
    if vlim is not None:
        amin, amax = vlim
    else:
        amin = arr.min()
        amax = arr.max()
    if amax > amin:
        arr = (arr - amin) / (amax - amin) * 255.0
    else:
        arr = np.zeros_like(arr)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    h, w = arr.shape
    img = QtGui.QImage(arr, w, h, QtGui.QImage.Format_Grayscale8)
    return img

from pathlib import Path
import os
import numpy as np
import nibabel as nib


def load_mri(path: str | Path | None = None) -> np.ndarray:
    """Load a NIfTI file using nibabel. If path is None, tries env MRI_PATH or default path.

    Returns a 3D numpy array (slices, H, W).
    """
    if path is None:
        path = os.environ.get('MRI_PATH', r"C:\Data\T1_post_grid_resample.nii.gz")
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    img = nib.load(path)
    arr = img.get_fdata()
    arr = np.transpose(arr, (1, 2, 0))[:, :, ::-1]  # reorient to (slices, H, W)
    if arr.ndim == 3:
        return np.asarray(arr, dtype=np.float32)
    elif arr.ndim == 4:
        return np.asarray(arr[..., 0], dtype=np.float32)
    else:
        raise ValueError(f"Unsupported NIfTI data shape: {arr.shape}")


def load_grid(path: str | Path | None = None) -> np.ndarray:
    """Load a tracts .npy mapping and normalize to (R, C, 2).

    If path is None, tries repo root `tracts.npy` and falls back to a synthetic mapping.
    """
    if path is None:
        # repo root two levels up
        here = Path(__file__).resolve().parents[1]
        p = here / 'tracts.npy'
        if p.exists():
            path = p
    if path is not None:
        path = Path(path)
        if path.exists():
            arr = np.load(path)
            
            return arr[:, ::-1]
    raise FileNotFoundError("No valid tracts.npy file found at the specified path.")

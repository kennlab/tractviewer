import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from matplotlib.widgets import RangeSlider, TextBox
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--no-post", action="store_true", help="Omit post-slice axis")
args = parser.parse_args()
NO_POST = args.no_post


# params
center = (261, 248)
initial_rect = 200, 320, 140, 250
tracts = np.load("tracts.npy")
img_pre_path = "T1_pre2post_grid_resample.nii.gz"
img_post_path = "T1_post_grid_resample.nii.gz"
SELECTED_LINE_WIDTH = 0.5
UNSELECTED_LINE_WIDTH = 0.5
MARKER_SIZE_5mm = 10
MARKER_SIZE_1mm = 3
ALPHA = 0.15
GRID_LIMS = [-12, -22, 12, 22]

img_pre = nib.load(img_pre_path)
img_pre_data = img_pre.get_fdata()

if not NO_POST:
    img_post = nib.load(img_post_path)
    img_post_data = img_post.get_fdata()

tracts_in_voxel_coords = tracts * 2  # Convert to voxel space (0.5 mm resolution)
tracts_in_voxel_coords += np.array(center)
rows = np.unique(tracts_in_voxel_coords[:, 0])

# Create figure with three axes
axes = {}
if NO_POST:
    fig, (axes['main'], axes['slices_pre']) = plt.subplots(1, 2, figsize=(10, 5), width_ratios=[1,3])
else:
    fig, (axes['main'], axes['slices_pre'], axes['slices_post']) = plt.subplots(1, 3, figsize=(15, 5), width_ratios=[1,3,3])
plt.subplots_adjust(bottom=0.25)  # Adjust layout to fit sliders and textboxes

axes['main'].scatter(tracts[:, 1], tracts[:, 0], c='r', s=10)
axes['main'].set_xlabel("Y Coordinate")
axes['main'].set_ylabel("X Coordinate")
axes['main'].set_title("Click on a tract to view slice")
axes['main'].set_xlim(GRID_LIMS[0], GRID_LIMS[2])
axes['main'].set_ylim(GRID_LIMS[1], GRID_LIMS[3])

axes['slices_pre'].set_title("Pre Image Slice")
if not NO_POST:
    axes['slices_post'].set_title("Post Image Slice")

# Contrast range slider
ax_slider = plt.axes([0.25, 0.1, 0.5, 0.03])
contrast_slider = RangeSlider(ax_slider, 'Contrast', 0, 500, valinit=(50, 200))

# Textboxes for setting x and y limits
ax_xmin = plt.axes([0.25, 0.02, 0.1, 0.05])
ax_xmax = plt.axes([0.37, 0.02, 0.1, 0.05])
ax_ymin = plt.axes([0.50, 0.02, 0.1, 0.05])
ax_ymax = plt.axes([0.62, 0.02, 0.1, 0.05])

XMIN_INIT, XMAX_INIT, YMIN_INIT, YMAX_INIT = list(map(str, initial_rect))
xmin_box = TextBox(ax_xmin, 'X Min', initial=XMIN_INIT)
xmax_box = TextBox(ax_xmax, 'X Max', initial=XMAX_INIT)
ymin_box = TextBox(ax_ymin, 'Y Min', initial=YMIN_INIT)
ymax_box = TextBox(ax_ymax, 'Y Max', initial=YMAX_INIT)

# Callback function for clicking on tracts
closest_idx, selected_row, selected_col = None, None, None
def on_click(event):
    global selected_row, selected_col, closest_idx
    if event.inaxes != axes['main']:
        return
    x_click, y_click = event.xdata, event.ydata
    
    if x_click is None or y_click is None:
        return
    
    # Find closest tract point
    distances = np.sqrt((tracts[:, 1] - x_click) ** 2 + (tracts[:, 0] - y_click) ** 2)
    closest_idx = np.argmin(distances)
    selected_row = int(tracts_in_voxel_coords[closest_idx, 0])
    selected_col = int(tracts_in_voxel_coords[closest_idx, 1])
    
    update_plot()

def update_plot(val=None):
    if selected_row is None or selected_col is None:
        return
    
    vmin, vmax = contrast_slider.val
    
    # Get limits from textboxes
    try:
        x_min, x_max = int(xmin_box.text), int(xmax_box.text)
        y_min, y_max = int(ymin_box.text), int(ymax_box.text)
    except ValueError:
        return  # If invalid input, do nothing
    
    # Update pre and post slice plots
    slices_to_update = ['slices_pre'] if NO_POST else ['slices_pre', 'slices_post']
    for slice_name in slices_to_update:
        ax = axes[slice_name]
        ax.clear()
        name = "Pre" if slice_name == 'slices_pre' else "Post"
        ax.set_title(f"{name} Image Slice at row {selected_row}")

        im = img_pre_data[:, selected_row, :] if slice_name == 'slices_pre' else img_post_data[:, selected_row, :]
        ax.imshow(np.flip(np.rot90(im)), cmap='gray', vmin=vmin, vmax=vmax)

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_max, y_min)
    
    # Highlight selected row in axes['main']
    axes['main'].clear()
    axes['main'].scatter(tracts[:, 1], tracts[:, 0], c='r', s=10)
    axes['main'].scatter(tracts[closest_idx, 1], tracts[closest_idx, 0], c='b', s=30)  # Highlight selected point in blue
    axes['main'].set_xlim(GRID_LIMS[0], GRID_LIMS[2])
    axes['main'].set_ylim(GRID_LIMS[1], GRID_LIMS[3])
    
    # Add transparent grid lines for all other tracts in the same row
    same_row_tracts = tracts_in_voxel_coords[tracts_in_voxel_coords[:, 0] == selected_row]
    for label in slices_to_update:
        ax = axes[label]
        ax.axvline(selected_col, color='r', lw=SELECTED_LINE_WIDTH)
        for y_coord in same_row_tracts[:, 1]:
            ax.axvline(y_coord, color='red', alpha=ALPHA, lw=UNSELECTED_LINE_WIDTH)
    mlcoords = np.unique(same_row_tracts[:, 1])
    dv_coords_5mm = np.arange(y_min, y_max, 5*2)
    dv_coords_1mm = np.arange(y_min, y_max, 1*2)
    scatter_coords_5mm_x, scatter_coords_5mm_y =np.meshgrid(mlcoords, dv_coords_5mm)
    scatter_coords_5mm_x = scatter_coords_5mm_x.flatten()
    scatter_coords_5mm_y = scatter_coords_5mm_y.flatten()

    scatter_coords_1mm_x, scatter_coords_1mm_y =np.meshgrid(mlcoords, dv_coords_1mm)
    scatter_coords_1mm_x = scatter_coords_1mm_x.flatten()
    scatter_coords_1mm_y = scatter_coords_1mm_y.flatten()

    for label in slices_to_update:
        ax = axes[label]
        ax.scatter(scatter_coords_5mm_x, scatter_coords_5mm_y, c='b', s=MARKER_SIZE_5mm, alpha=1, zorder=100)
        ax.scatter(scatter_coords_1mm_x, scatter_coords_1mm_y, c='r', s=MARKER_SIZE_1mm, alpha=1, zorder=100)

    axes['main'].set_xlabel("Y Coordinate")
    axes['main'].set_ylabel("X Coordinate")
    axes['main'].set_title("Click on a tract to view slice")
    
    fig.canvas.draw()

fig.canvas.mpl_connect('button_press_event', on_click)
contrast_slider.on_changed(update_plot)
xmin_box.on_submit(update_plot)
xmax_box.on_submit(update_plot)
ymin_box.on_submit(update_plot)
ymax_box.on_submit(update_plot)
fig.tight_layout(rect=[0, .15, 1, 1])
plt.show()
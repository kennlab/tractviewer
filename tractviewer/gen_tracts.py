import numpy as np


# default
AP = np.arange(-20.5, 21, 1)
ML = np.arange(-11, 12, 1)
ap, ml = np.meshgrid(AP, ML)


# # today
# ap = np.array([-5, -5, -5, -5, -8, -8, -8, -8]) + .5
# ml = np.array([-6, -5, -3, -2, -7, -6, -4, -3])
# tracts = np.stack([ap.flatten(), ml.flatten()]).T

# ap = np.array([12, 12, 12, 12])-.5
# ml = np.array([3, 4, 5, 6])
tracts = np.stack([ap.flatten(), ml.flatten()]).T


# x = [np.arange(7.5, 21, .5), 
np.save('tracts.npy', tracts)
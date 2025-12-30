import cv2
import numpy as np

depth = cv2.imread("depth_raw.png", cv2.IMREAD_UNCHANGED)

print("Depth dtype: ", depth.dtype)   # uint16
print("Depth shape: ", depth.shape)   # (480, 640)
print("Depth min: ", depth.min())
print("Depth max: ", depth.max())

depth_vis = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX)
depth_vis = depth_vis.astype(np.uint8)
cv2.imwrite("depth_vis.png", depth_vis)

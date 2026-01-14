import pyrealsense2 as rs
import numpy as np
import cv2
import os
from PIL import Image
import math
from decimal import Decimal, ROUND_HALF_UP
import time


# License: Apache 2.0. See LICENSE file in root directory.
# Copyright(c) 2025 RealSense, Inc. All Rights Reserved.

import numpy as np
import pyrealsense2 as rs
import cv2

import matplotlib.pyplot as plt

depth_width, depth_height = 1280, 720
color_width, color_height = 1280, 720
ratio = depth_width / color_width
color_cam_path = "/dev/video6"
FPS = 30
# Directory to save images
output_dir = "realsense_captures"
os.makedirs(output_dir, exist_ok=True)

pipeline = rs.pipeline()
config = rs.config()

# Get device product line for setting a supporting resolution
pipeline_wrapper = rs.pipeline_wrapper(pipeline)
print(f"Pipeline wrapper: {pipeline_wrapper}")
pipeline_profile = config.resolve(pipeline_wrapper)
print(f"Pipeline profile: {pipeline_profile}")
device = pipeline_profile.get_device()
print(f"Device: {device}")
device_product_line = str(device.get_info(rs.camera_info.product_line))
print(f"Device product line: {device_product_line}")

found_rgb = False
for s in device.sensors:
    print(f"Sensor: {s}")
    if s.get_info(rs.camera_info.name) == 'RGB Camera':
        found_rgb = True
        break
if not found_rgb:
    print("The demo requires Depth camera with Color sensor")
    exit(0)

config.enable_stream(rs.stream.depth, depth_width, depth_height, rs.format.z16, FPS)
config.enable_stream(rs.stream.color, color_width, color_height, rs.format.bgr8, FPS)

profile = pipeline.start(config)




align_to = rs.stream.color
align = rs.align(align_to)

# get camera intrinsics
intr = profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
print(f"Depth camera intrinsics: {intr}")



# # COLOR CAMERA
# cap = cv2.VideoCapture("/dev/video6", cv2.CAP_V4L2)

# if not cap.isOpened():
#     print("Error: Could not open video device")
#     raise ValueError("Could not open video device")

# cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, color_width)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, color_height)
# color_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
# color_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
# print(f"Color camera resolution: {int(color_width)}x{int(color_height)}")


# # Wait for camera to be ready
# start_time = time.time()
# while time.time() - start_time < 5:
#     ret, frame = cap.read()
#     time.sleep(0.1)
# print("Camera ready")




counter = 0
while counter < 10:

    # Wait for a coherent pair of frames: depth and color
    frames = pipeline.wait_for_frames()
    aligned_frames = align.process(frames)
    
    # ret, color_image = cap.read()
    # if not ret:
    #     print("Error: Could not read color image")
    #     break
    
    color_image = aligned_frames.get_color_frame()
    if not color_image:
        print("Error: Could not read color image")
        break

    color_image = np.asanyarray(color_image.get_data())
    
    
    

    color_rgb = color_image[:, :, ::-1]
    img_pil_ = Image.fromarray(color_rgb)
    img_pil_.save(os.path.join(output_dir, f"color_rgb_{counter:06d}.png"))

    

    
    print(f"Color image shape: {color_image.shape}")
    print(f"Color image dtype: {color_image.dtype}")
    print(f"Color image min: {np.min(color_image)}")
    print(f"Color image max: {np.max(color_image)}")

    # Get depth frame and convert to numpy array
    depth_frame = aligned_frames.get_depth_frame()
    depth_image = np.asanyarray(depth_frame.get_data())
    print(f"Depth image shape: {depth_image.shape}")
    print(f"Depth image dtype: {depth_image.dtype}")
    print(f"Depth image min: {np.min(depth_image)}")
    print(f"Depth image max: {np.max(depth_image)}")

    if not isinstance(depth_image, np.ndarray):
        raise TypeError("Depth image is not a numpy array.")
    

    u_color, v_color = int(color_width / 2 + counter * 2), int(color_height / 2 + counter * 2)
    u_depth, v_depth = int(depth_width / 2 + counter * 2), int(depth_height / 2 + counter * 2)
    
    

    dist = depth_frame.get_distance(u_depth, v_depth) * 1000 # Chuyển sang mm

    Xtemp = dist * (u_depth - intr.ppx) / intr.fx
    Ytemp = dist * (v_depth - intr.ppy) / intr.fy
    Ztemp = dist
    
    print(f"Xtemp: {Xtemp}, Ytemp: {Ytemp}, Ztemp: {Ztemp}")


    theta = 0
    print(f"Theta: {theta}")
    Xtarget = Xtemp - 35  # Bù 35mm sai lệch trục X
    Ytarget = -(Ztemp * math.sin(theta) + Ytemp * math.cos(theta))
    Ztarget = Ztemp * math.cos(theta) + Ytemp * math.sin(theta)
    print(f"Xtarget: {Xtarget}, Ytarget: {Ytarget}, Ztarget: {Ztarget}")
    
    
    coordinates_text = "(" + str(Decimal(str(Xtarget)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)) + \
                                ", " + str(Decimal(str(Ytarget)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)) + \
                                ", " + str(Decimal(str(Ztarget)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)) + ")"

    print(f"Coordinates: {coordinates_text}")
    
    # cv2.putText(color_image, coordinates_text, (u_color, v_color), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    # cv2.imwrite(os.path.join(output_dir, f"color_{counter:06d}.png"), color_image)
    
    counter += 1

pipeline.stop()
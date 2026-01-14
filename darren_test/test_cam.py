import cv2
import os
import time


def main():
    out_path = "imgs/video6"
    os.makedirs(out_path, exist_ok=True)
    cap = cv2.VideoCapture("/dev/video6", cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print("Error: Could not open video device")
        return
    
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2560)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1440)
    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Resolution: {int(w)}x{int(h)}")
    
    # Wait for camera to be ready
    start_time = time.time()
    while time.time() - start_time < 5:
        ret, frame = cap.read()
        time.sleep(0.1)
    print("Camera ready")

    cnt = 0
    start_time = time.time()
    while cnt < 20:
        ret, frame = cap.read()
        if not ret:
            break
        print(f"Frame {cnt:04d} captured, time: {time.time() - start_time:.2f}s")
        cv2.imwrite(os.path.join(out_path, f"cam_0_{cnt:04d}.png"), frame)
        time.sleep(0.5)
        cnt += 1
    cap.release()

if __name__ == "__main__":
    main()

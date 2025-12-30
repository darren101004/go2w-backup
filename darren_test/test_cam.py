import cv2
import os
import time

def capture_from_cameras(cam_indices, convert_to_bgr, root_img_dir):
    save_dirs = [os.path.join(root_img_dir, f"capture{cam_idx}") for cam_idx in cam_indices]
    for d in save_dirs:
        os.makedirs(d, exist_ok=True)

    caps = [cv2.VideoCapture(cam_idx) for cam_idx in cam_indices]
    for idx, cap in zip(cam_indices, caps):
        if not cap.isOpened():
            print(f"Failed to open camera at index {idx}")

    img_counts = [0 for _ in cam_indices]
    print(f"Starting capture from cameras {cam_indices}. Images will be saved in '{root_img_dir}'.")
    try:
        cnt = 0
        while True:
            for i, (cap, cam_idx, save_dir, convert_to_bgr_i) in enumerate(zip(caps, cam_indices, save_dirs, convert_to_bgr)):
                if not cap.isOpened():
                    continue
                ret, frame = cap.read()
                print("frame.shape:", frame.shape)
                print("frame.dtype:", frame.dtype)
                print("mean of each channel:", frame.mean(axis=(0,1)))
                if convert_to_bgr_i:
                    try:
                        frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_UYVY)
                    except:
                        pass
                if not ret:
                    print(f"Failed to read frame from camera {cam_idx}.")
                    continue
                img_path = os.path.join(save_dir, f"cam{cam_idx}_img{img_counts[i]:04d}.jpg")
                cv2.imwrite("test_cam.jpg", frame)
                print(f"Cam{cam_idx}: Saved {img_path}")
                img_counts[i] += 1
            time.sleep(0.5)
            cnt += 1
            if cnt > 10:
                break
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Stopping all camera captures...")
    finally:
        for cap, cam_idx in zip(caps, cam_indices):
            cap.release()
            print(f"Capture from camera {cam_idx} stopped.")

def main():
    cam_indices = [4]
    convert_to_bgr = [True]
    root_img_dir = "test_captures"
    if os.path.exists(root_img_dir):
        import shutil
        shutil.rmtree(root_img_dir)
    os.makedirs(root_img_dir, exist_ok=True)
    print(f"Cameras to use: {cam_indices}")
    print(f"Root images dir: {root_img_dir}")
    capture_from_cameras(cam_indices, convert_to_bgr, root_img_dir)
    print("All camera captures stopped.")

if __name__ == "__main__":
    main()

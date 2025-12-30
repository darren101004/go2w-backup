import time
import os
import sys

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.video.video_client import VideoClient

if __name__ == "__main__":
    img_dir = "imgs"
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    if len(sys.argv) > 1:
        ChannelFactoryInitialize(0, sys.argv[1])
    else:
        ChannelFactoryInitialize(0)

    client = VideoClient()
    client.SetTimeout(3.0)
    client.Init()

    print("##################Continuous Image Capture###################")

    img_idx = 0
    try:
        while True:
            code, data = client.GetImageSample()
            print(f"code: {code}, data length: {len(data)}")
            if code != 0:
                print("get image sample error. code:", code)
            else:
                image_name = os.path.join(img_dir, f"img_{img_idx:05d}.jpg")
                try:
                    with open(image_name, "wb") as f:
                        f.write(bytes(data))
                    print(f"Saved image: {image_name}")
                except Exception as e:
                    print("save image error. error:", e)
                img_idx += 1
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Capture stopped by user.")


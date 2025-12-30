
import time
import sys
import signal
import logging

from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.unitree_go.msg.dds_ import HeightMap_

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

running = True

def sigint_handler(sig, frame):
    global running
    logging.info("Stopping by user request (SIGINT)...")
    running = False

signal.signal(signal.SIGINT, sigint_handler)




import time
import sys

from unitree_sdk2py.core.channel import ChannelPublisher, ChannelFactoryInitialize
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.std_msgs.msg.dds_ import String_
from unitree_sdk2py.idl.default import std_msgs_msg_dds__String_

class Custom:
    def __init__(self):
        # create publisher #
        self.publisher = ChannelPublisher("rt/utlidar/switch", String_)
        self.publisher.Init()
        self.low_cmd = std_msgs_msg_dds__String_()   

    def go2_utlidar_switch(self,status):
        if status == "OFF":
            self.low_cmd.data = "OFF"
        elif status == "ON":
            self.low_cmd.data = "ON"

        self.publisher.Write(self.low_cmd)
        



TOPIC_CLOUD = "rt/utlidar/height_map_array"

class StateReader:
    def __init__(self):
        self.last_print = 0

    def Init(self):
        logging.info(f"Initializing channel subscriber for topic: {TOPIC_CLOUD}")
        self.sub = ChannelSubscriber(TOPIC_CLOUD, HeightMap_)
        self.sub.Init(self.StateCallback, 10)
        logging.info("Channel subscriber initialized.")

    def StateCallback(self, msg: HeightMap_):
        now = time.time()
        if now - self.last_print < 0.2:
            return
        self.last_print = now

        logging.info("Received a HeightMap message:")
        logging.debug(f"Full HeightMap message: {msg}")
        print(
            f"\n\tstamp = {msg.stamp}"
            f"\n\tframe = {msg.frame_id}"
            f"\n\twidth = {msg.width}"
            f"\n\theight = {msg.height}"
            f"\n\tresolution = {msg.resolution}\n"
        )


if __name__ == "__main__":
    logging.info("Reading GO2 robot state (HeightMap topic)...")
    print("Press Ctrl+C to exit.\n")

    # Initialize DDS
    if len(sys.argv) > 1:
        iface = sys.argv[1]
        logging.info(f"Using network interface: {iface}")
        ChannelFactoryInitialize(0, iface)
    else:
        logging.info("Using default network interface")
        ChannelFactoryInitialize(0)

    custom = Custom()
    custom.go2_utlidar_switch("ON")

    reader = StateReader()
    reader.Init()

    # Keep process alive
    logging.info("Start waiting for HeightMap data...")
    while running:
        time.sleep(0.1)

    logging.info("Exited cleanly.")

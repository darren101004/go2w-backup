# import sys
# import time
# from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_, LowState_
# from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize



# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         interface = "eth0"
#     else:
#         interface = sys.argv[1]
#     try:
#         ChannelFactoryInitialize(0, interface)
#         time.sleep(1)
#         TOPIC_STATE = "rt/lowstate"
#         sub = ChannelSubscriber(TOPIC_STATE, LowState_)
#         sub.Init()
        
        
#         while True:
#             msg: LowState_ = sub.Read(timeout=1.0)
#             if msg is not None:
#                 print("Received LowState: ", msg)
#             time.sleep(1)
#             if KeyboardInterrupt:
#                 break
#     except KeyboardInterrupt:
#         print("\nReceived keyboard interrupt (Ctrl+C), exiting gracefully.")
#         sys.exit(0)
import time
import sys
import signal

from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_

running = True

def sigint_handler(sig, frame):
    global running
    print("\nStopping...")
    running = False

signal.signal(signal.SIGINT, sigint_handler)


class StateReader:
    def __init__(self):
        self.last_print = 0

    def Init(self):
        # rt/sportmodestate có tần số cao, dùng callback để nhận real-time
        self.sub = ChannelSubscriber("rt/sportmodestate", SportModeState_)
        self.sub.Init(self.StateCallback, 10)

    def StateCallback(self, msg: SportModeState_):
        # Giảm tần suất in (chỉ in mỗi 0.2s)
        now = time.time()
        if now - self.last_print < 0.2:
            return
        self.last_print = now

        print("=" * 80)
        print(" 🟦 SPORT MODE STATE")
        print(f"  Sport mode state: {msg}")
        print("=" * 80)


if __name__ == "__main__":
    print("Reading GO2 robot state...")
    print("Press Ctrl+C to exit.\n")

    # Initialize DDS
    if len(sys.argv) > 1:
        ChannelFactoryInitialize(0, sys.argv[1])
    else:
        ChannelFactoryInitialize(0)

    reader = StateReader()
    reader.Init()

    # Keep process alive
    while running:
        time.sleep(0.1)

    print("Exited cleanly.")

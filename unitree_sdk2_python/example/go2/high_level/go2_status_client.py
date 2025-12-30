# import time
# import sys
# from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
# from unitree_sdk2py.go2.sport.sport_client import SportClient
# from unitree_sdk2py.idl.default import unitree_go_msg_dds__SportModeState_
# from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_
# from unitree_sdk2py.go2.robot_state.robot_state_client import (
#     RobotStateClient,
#     ServiceState
# )


# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         interface = "eth0"
#     else:
#         interface = sys.argv[1]
#     ChannelFactoryInitialize(0, interface)
#     rsc = RobotStateClient()
#     rsc.SetTimeout(3.0)
#     rsc.Init()
    
#     sport_client = SportClient()  
#     sport_client.SetTimeout(10.0)
#     sport_client.Init()
    

#     while True:
#         print("##################GetServerApiVersion###################")
#         code, serverApiVersion = rsc.GetServerApiVersion()
#         if code != 0:
#             print("GetServerApiVersion failed, code: ", code)
#             continue
#         print("ServerApiVersion: ", serverApiVersion)
#         time.sleep(3)
        
#         print("##################ServiceList###################")
#         sport_client.StandUp()   
#         print("##################ServiceSwitch###################")
#         # code = rsc.ServiceSwitch("wheeled_sport", False)
#         # if code != 0:
#         #     print("service stop sport_mode error. code:", code)
#         # else:
#         #     print("service stop sport_mode success. code:", code)

#         # time.sleep(1)

#         code = rsc.ServiceSwitch("wheeled_sport", True)
#         if code != 0:
#             print("service start sport_mode error. code:", code)
#         else:
#             print("service start sport_mode success. code:", code)
        
#         sport_client.StandDown()
#         time.sleep(3)
        
        
        
import time
import sys

from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowState_
from unitree_sdk2py.go2.sport.sport_client import SportClient


class StateReader:
    def __init__(self):
        self.low_state = None

    def Init(self):
        # subscribe to /rt/lowstate
        self.lowstate_sub = ChannelSubscriber("rt/lowstate", LowState_)
        self.lowstate_sub.Init(self.StateCallback, 10)

    def StateCallback(self, msg: LowState_):
        self.low_state = msg

        # In ra thông tin quan trọng
        import math
        def quat_to_euler(w, x, y, z):
            # Roll (nghiêng trái/phải)
            sinr = 2 * (w*x + y*z)
            cosr = 1 - 2 * (x*x + y*y)
            roll = math.atan2(sinr, cosr)

            # Pitch (cúi/ngửa)
            sinp = 2 * (w*y - z*x)
            pitch = math.asin(max(-1, min(1, sinp)))

            # Yaw (xoay hướng)
            siny = 2 * (w*z + x*y)
            cosy = 1 - 2 * (y*y + z*z)
            yaw = math.atan2(siny, cosy)

            return roll, pitch, yaw
        w, x, y, z = msg.imu_state.quaternion
        roll, pitch, yaw = quat_to_euler(w, x, y, z)
        print(f"=" * 100)
        print("IMU:")
        print(f"  Quaternion (w,x,y,z): {w}, {x}, {y}, {z}")
        # print(f"  Roll, Pitch, Yaw: {roll}, {pitch}, {yaw}")
        print("=" * 100)
        print("Motor states:")
        # for i, m in enumerate(msg.motor_state[:12]):
        #     print(f"  Joint {i}: q={m.q:.3f}, dq={m.dq:.3f}, tau={m.tau:.3f}")
        print(f"  Motor state: {msg.motor_state}")
        print("=" * 100)


if __name__ == "__main__":

    print("Reading GO2 robot state...")
    print("Press Ctrl+C to exit.")
    
    # sport_client = SportClient()
    # sport_client.SetTimeout(10.0)
    # sport_client.Init()
    
    # sport_client.StandUp()
    # time.sleep(1)   
    # sport_client.StandDown()
    # time.sleep(3)

    # DDS init
    if len(sys.argv) > 1:
        ChannelFactoryInitialize(0, sys.argv[1])
    else:
        ChannelFactoryInitialize(0)

    reader = StateReader()
    reader.Init()

    # Loop chờ callback
    while True:
        time.sleep(0.1)

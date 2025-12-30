import time
import sys
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.default import unitree_go_msg_dds__SportModeState_
from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_
from unitree_sdk2py.go2.sport.sport_client import (
    SportClient,
    PathPoint,
    SPORT_PATH_POINT_SIZE,
)
import math
from dataclasses import dataclass
from unitree_sdk2py.go2.robot_state.robot_state_client import (
    RobotStateClient,
)
if __name__ == "__main__":

    ChannelFactoryInitialize(0, "eth0")

    print("Initializing sport client...")
    sport_client = SportClient() 
     
    sport_client.SetTimeout(10.0)
    print("Initializing sport client...")
    sport_client.Init()
    time.sleep(1)
    
    print("Recovery stand...")
    res = sport_client.RecoveryStand()
    print(f"Recovery stand result: {res}")
    time.sleep(2)
    res = sport_client.BalanceStand()
    print(f"Balance stand result: {res}")
    time.sleep(2)
    # # Quay (spin) for 5 seconds: rotate in place with angular speed 0.3 rad/s
    # start_time = time.time()
    # while time.time() - start_time < 5:
    #     res = sport_client.Move(0, 0, 0.3)
    #     print(f"Spin in place result: {res}")
    #     time.sleep(1)
    # res = sport_client.StopMove()
    # print(f"Stop move result: {res}")
    
    # res = sport_client.StandUp()
    # print(f"Stand up result: {res}")
    # time.sleep(5)
    # res = sport_client.StandDown()
    # print(f"Stand down result: {res}")
    # time.sleep(5)
    # res = sport_client.StandUp()
    # print(f"Stand up result: {res}")
    # time.sleep(2)
    # res = sport_client.BalanceStand()
    # print(f"Balance stand result: {res}")
    # time.sleep(2)
    
    start_time = time.time()
    while time.time() - start_time < 2:
        res = sport_client.Move(0.5, 0, 0)
        print(f"Move result: {res}")
        time.sleep(0.5)
    res = sport_client.StopMove()
    print(f"Stop move result: {res}")
    res = sport_client.StandUp()
    print(f"Stand up result: {res}")
    time.sleep(3)
    res = sport_client.StandDown()
    print(f"Stand down result: {res}")
    time.sleep(5)
    res = sport_client.Damp()
    print(f"Damp result: {res}")
    
    time.sleep(2)
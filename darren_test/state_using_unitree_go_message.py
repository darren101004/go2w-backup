#!/usr/bin/env python3

import threading
import logging
import uvicorn

import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
from fastapi.concurrency import asynccontextmanager
from contextlib import AsyncExitStack

from fastmcp import FastMCP
from fastapi import FastAPI
from unitree_go.msg import SportModeState

logger = logging.getLogger(__name__)

# In-memory storage for latest state
_latest_state_lock = threading.Lock()
_latest_state = {}

class SportStateSubscriber(Node):
    def __init__(self):
        super().__init__('sport_state_mcp_subscriber')
        self.subscription = self.create_subscription(
            SportModeState,
            '/lf/sportmodestate',
            self.listener_callback,
            10
        )
        logger.info('SportState MCP Subscriber đã khởi động!')

    def listener_callback(self, msg):
        logger.info(f"State updated: {msg}")
        global _latest_state
        state = {
            "imu_state": {
                "quaternion": list(msg.imu_state.quaternion),
                "gyroscope": list(msg.imu_state.gyroscope),
                "accelerometer": list(msg.imu_state.accelerometer),
                "rpy": list(msg.imu_state.rpy),
                "temperature": msg.imu_state.temperature
            },
            "position": list(msg.position),
            "body_height": msg.body_height,
            "velocity": list(msg.velocity),
            "yaw_speed": msg.yaw_speed,
            "foot_force": list(msg.foot_force),
            "mode": msg.mode,
        }
        with _latest_state_lock:
            _latest_state = state
        logger.debug(f"State updated: {state}")

# --- MCP Server wrapping ---

mcp = FastMCP("go2_state_sample")

_subscriber = None
_executor = None

def ensure_background_ros_spin():
    global _subscriber, _executor
    if _subscriber is not None:
        return

    rclpy.init(args=None)
    _subscriber = SportStateSubscriber()
    _executor = SingleThreadedExecutor()
    _executor.add_node(_subscriber)

    spin_thread = threading.Thread(target=_executor.spin, daemon=True)
    spin_thread.start()
    logger.info("Started SportStateSubscriber in background thread")

@mcp.tool(description="Lấy trạng thái SportMode của robot (go2)")
async def get_sport_mode_state() :
    ensure_background_ros_spin()
    with _latest_state_lock:
        state = _latest_state.copy()

    logger.info(f"State: {state}")
    return {
        "success": True,
        "message": "State OK",
        "data": state
 
    }
    
    
mcp_http = mcp.http_app(
    path="/state",
    middleware=[],
    stateless_http=True,
)


@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    try:
        logger.info(
            "Initialize all singleton services at application startup."
        )

        async with AsyncExitStack() as stack:
            for mcp in [
                mcp_http,
            ]:
                logger.info(f"Entering lifespan for {mcp.__module__}")
                await stack.enter_async_context(mcp.lifespan(app))

            yield
    finally:
        pass



app = FastAPI(name="go2_state_sample", lifespan=combined_lifespan)

app.mount(
    "/mcp",
    mcp_http,
    name="mcp",
)

if __name__ == '__main__':
    # This will start the MCP server
    uvicorn.run(app, host="0.0.0.0", port=8005)
#!/usr/bin/env python3

"""
Define SportModeState message structure trong Python và subscribe
Không cần build ROS package
"""

import rclpy
from rclpy.node import Node
from rosidl_runtime_py.utilities import get_message


# ============================================
# ĐỊNH NGHĨA MESSAGE STRUCTURES
# ============================================

class TimeSpec:
    """Time specification"""
    def __init__(self):
        self.sec = 0          # int32
        self.nanosec = 0      # uint32


class IMUState:
    """IMU State data"""
    def __init__(self):
        self.quaternion = [0.0, 0.0, 0.0, 0.0]       # float32[4]
        self.gyroscope = [0.0, 0.0, 0.0]             # float32[3]
        self.accelerometer = [0.0, 0.0, 0.0]         # float32[3]
        self.rpy = [0.0, 0.0, 0.0]                   # float32[3] - Roll, Pitch, Yaw
        self.temperature = 0                          # int8


class SportModeState:
    """Sport Mode State message - Định nghĩa chính xác theo interface"""
    def __init__(self):
        # Timestamp
        self.stamp = TimeSpec()                       # TimeSpec
        
        # Error code
        self.error_code = 0                           # uint32
        
        # IMU data
        self.imu_state = IMUState()                   # IMUState
        
        # Mode and gait
        self.mode = 0                                 # uint8
        self.progress = 0.0                           # float32
        self.gait_type = 0                            # uint8
        self.foot_raise_height = 0.0                  # float32
        
        # Position and velocity
        self.position = [0.0, 0.0, 0.0]              # float32[3]
        self.body_height = 0.0                        # float32
        self.velocity = [0.0, 0.0, 0.0]              # float32[3]
        self.yaw_speed = 0.0                          # float32
        
        # Obstacle detection
        self.range_obstacle = [0.0, 0.0, 0.0, 0.0]   # float32[4]
        
        # Foot information
        self.foot_force = [0, 0, 0, 0]                # int16[4]
        self.foot_position_body = [0.0] * 12          # float32[12]
        self.foot_speed_body = [0.0] * 12             # float32[12]
    
    def __repr__(self):
        return (f"SportModeState(\n"
                f"  mode={self.mode},\n"
                f"  position={self.position},\n"
                f"  velocity={self.velocity},\n"
                f"  RPY={self.imu_state.rpy}\n"
                f")")


# ============================================
# ROS2 SUBSCRIBER
# ============================================

class SportModeStateSubscriber(Node):
    def __init__(self):
        super().__init__('sport_mode_state_subscriber')
        
        # Topic name
        self.topic_name = '/lf/sportmodestate'
        
        # Lấy message type từ topic
        msg_type_str = self.get_topic_type(self.topic_name)
        
        if msg_type_str is None:
            self.get_logger().error(f'❌ Topic {self.topic_name} không tồn tại!')
            self.get_logger().info('💡 Kiểm tra: ros2 topic list')
            return
        
        self.get_logger().info(f'✅ Detected message type: {msg_type_str}')
        
        # Tạo subscription
        self.subscription = self.create_subscription(
            get_message(msg_type_str),
            self.topic_name,
            self.listener_callback,
            10
        )
        
        self.get_logger().info(f'🚀 Subscriber đã khởi động! Đang lắng nghe {self.topic_name}')

    def get_topic_type(self, topic_name):
        """Lấy message type từ topic đang chạy"""
        topic_names_and_types = self.get_topic_names_and_types()
        
        for name, types in topic_names_and_types:
            if name == topic_name:
                return types[0] if types else None
        return None

    def listener_callback(self, ros_msg):
        """
        Callback nhận ROS message và convert sang custom class
        """
        # Convert sang custom class
        msg = self.convert_to_custom(ros_msg)
        
        # Hiển thị thông tin
        self.display_message(msg)

    def convert_to_custom(self, ros_msg):
        """
        Chuyển ROS message sang custom SportModeState class
        """
        msg = SportModeState()
        
        try:
            # Timestamp
            if hasattr(ros_msg, 'stamp'):
                msg.stamp.sec = getattr(ros_msg.stamp, 'sec', 0)
                msg.stamp.nanosec = getattr(ros_msg.stamp, 'nanosec', 0)
            
            # Error code
            msg.error_code = getattr(ros_msg, 'error_code', 0)
            
            # IMU State
            if hasattr(ros_msg, 'imu_state'):
                imu = ros_msg.imu_state
                msg.imu_state.quaternion = list(getattr(imu, 'quaternion', [0.0]*4))
                msg.imu_state.gyroscope = list(getattr(imu, 'gyroscope', [0.0]*3))
                msg.imu_state.accelerometer = list(getattr(imu, 'accelerometer', [0.0]*3))
                msg.imu_state.rpy = list(getattr(imu, 'rpy', [0.0]*3))
                msg.imu_state.temperature = getattr(imu, 'temperature', 0)
            
            # Mode and gait
            msg.mode = getattr(ros_msg, 'mode', 0)
            msg.progress = getattr(ros_msg, 'progress', 0.0)
            msg.gait_type = getattr(ros_msg, 'gait_type', 0)
            msg.foot_raise_height = getattr(ros_msg, 'foot_raise_height', 0.0)
            
            # Position and velocity
            msg.position = list(getattr(ros_msg, 'position', [0.0]*3))
            msg.body_height = getattr(ros_msg, 'body_height', 0.0)
            msg.velocity = list(getattr(ros_msg, 'velocity', [0.0]*3))
            msg.yaw_speed = getattr(ros_msg, 'yaw_speed', 0.0)
            
            # Obstacle and foot data
            msg.range_obstacle = list(getattr(ros_msg, 'range_obstacle', [0.0]*4))
            msg.foot_force = list(getattr(ros_msg, 'foot_force', [0]*4))
            msg.foot_position_body = list(getattr(ros_msg, 'foot_position_body', [0.0]*12))
            msg.foot_speed_body = list(getattr(ros_msg, 'foot_speed_body', [0.0]*12))
            
        except Exception as e:
            self.get_logger().error(f'❌ Lỗi convert message: {e}')
        
        return msg

    def display_message(self, msg):
        """
        Hiển thị thông tin message theo cách dễ đọc
        """
        self.get_logger().info('=' * 70)
        self.get_logger().info('📊 SPORT MODE STATE')
        self.get_logger().info('=' * 70)
        
        # Timestamp
        self.get_logger().info(f'⏱️  Timestamp: {msg.stamp.sec}.{msg.stamp.nanosec:09d}s')
        self.get_logger().info(f'⚠️  Error Code: {msg.error_code}')
        
        # IMU Data
        self.get_logger().info('\n🧭 IMU STATE:')
        self.get_logger().info(f'  Roll:  {msg.imu_state.rpy[0]:8.4f} rad ({msg.imu_state.rpy[0]*57.2958:7.2f}°)')
        self.get_logger().info(f'  Pitch: {msg.imu_state.rpy[1]:8.4f} rad ({msg.imu_state.rpy[1]*57.2958:7.2f}°)')
        self.get_logger().info(f'  Yaw:   {msg.imu_state.rpy[2]:8.4f} rad ({msg.imu_state.rpy[2]*57.2958:7.2f}°)')
        self.get_logger().info(f'  Quaternion: [{msg.imu_state.quaternion[0]:.3f}, {msg.imu_state.quaternion[1]:.3f}, '
                             f'{msg.imu_state.quaternion[2]:.3f}, {msg.imu_state.quaternion[3]:.3f}]')
        self.get_logger().info(f'  Gyroscope: {[f"{x:.3f}" for x in msg.imu_state.gyroscope]}')
        self.get_logger().info(f'  Accelerometer: {[f"{x:.3f}" for x in msg.imu_state.accelerometer]}')
        self.get_logger().info(f'  🌡️  Temperature: {msg.imu_state.temperature}°C')
        
        # Mode and Gait
        self.get_logger().info(f'\n🤖 MODE & GAIT:')
        self.get_logger().info(f'  Mode: {msg.mode}')
        self.get_logger().info(f'  Gait Type: {msg.gait_type}')
        self.get_logger().info(f'  Progress: {msg.progress:.2f}')
        self.get_logger().info(f'  Foot Raise Height: {msg.foot_raise_height:.3f}m')
        
        # Position & Velocity
        self.get_logger().info(f'\n📍 POSITION & VELOCITY:')
        self.get_logger().info(f'  Position: [{msg.position[0]:.3f}, {msg.position[1]:.3f}, {msg.position[2]:.3f}]m')
        self.get_logger().info(f'  Body Height: {msg.body_height:.3f}m')
        self.get_logger().info(f'  Velocity: [{msg.velocity[0]:.3f}, {msg.velocity[1]:.3f}, {msg.velocity[2]:.3f}]m/s')
        self.get_logger().info(f'  Yaw Speed: {msg.yaw_speed:.3f}rad/s')
        
        # Foot Information
        self.get_logger().info(f'\n🦶 FOOT INFORMATION:')
        foot_names = ['FL', 'FR', 'RL', 'RR']  # Front-Left, Front-Right, Rear-Left, Rear-Right
        for i, name in enumerate(foot_names):
            self.get_logger().info(f'  {name}: Force={msg.foot_force[i]:4d}N')
        
        # Obstacle Detection
        self.get_logger().info(f'\n🚧 OBSTACLE RANGE: {[f"{x:.2f}" for x in msg.range_obstacle]}m')
        
        self.get_logger().info('=' * 70 + '\n')


# ============================================
# MAIN FUNCTION
# ============================================

def main(args=None):
    rclpy.init(args=args)
    
    subscriber = SportModeStateSubscriber()
    
    try:
        rclpy.spin(subscriber)
    except KeyboardInterrupt:
        print('\n👋 Đã dừng subscriber')
    finally:
        subscriber.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
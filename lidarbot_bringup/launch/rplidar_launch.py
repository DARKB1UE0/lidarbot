
# 本launch文件用于启动rplidar_ros节点，并配置相关参数

#!/usr/bin/env python3

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node



def generate_launch_description():
    # 定义可通过命令行传入的参数（LaunchConfiguration）
    channel_type =  LaunchConfiguration('channel_type', default='serial')         # 通信类型（串口/网口）
    serial_port = LaunchConfiguration('serial_port', default='/dev/ttyUSB0')      # 串口设备名
    serial_baudrate = LaunchConfiguration('serial_baudrate', default='115200')    # 串口波特率
    frame_id = LaunchConfiguration('frame_id', default='lidar_link')              # 激光雷达TF坐标系
    inverted = LaunchConfiguration('inverted', default='false')                   # 是否反转数据
    angle_compensate = LaunchConfiguration('angle_compensate', default='true')    # 是否角度补偿
    scan_mode = LaunchConfiguration('scan_mode', default='Standard')              # 扫描模式

    # 返回LaunchDescription对象，包含参数声明和节点启动
    return LaunchDescription([


        # 声明可配置参数，支持命令行覆盖
        DeclareLaunchArgument(
            'channel_type',
            default_value=channel_type,
            description='指定雷达通信类型（serial/udp等）'),
        DeclareLaunchArgument(
            'serial_port',
            default_value=serial_port,
            description='指定连接雷达的串口设备'),
        DeclareLaunchArgument(
            'serial_baudrate',
            default_value=serial_baudrate,
            description='指定串口波特率'),
        DeclareLaunchArgument(
            'frame_id',
            default_value=frame_id,
            description='指定雷达数据的TF坐标系'),
        DeclareLaunchArgument(
            'inverted',
            default_value=inverted,
            description='是否反转扫描数据'),
        DeclareLaunchArgument(
            'angle_compensate',
            default_value=angle_compensate,
            description='是否对扫描数据进行角度补偿'),
        DeclareLaunchArgument(
            'scan_mode',
            default_value=scan_mode,
            description='指定雷达扫描模式'),

        # 启动rplidar_ros节点，参数由上面配置传入
        Node(
            package='rplidar_ros',
            executable='rplidar_node',
            name='rplidar_node',
            parameters=[{
                'channel_type': channel_type,
                'serial_port': serial_port,
                'serial_baudrate': serial_baudrate,
                'frame_id': frame_id,
                'inverted': inverted,
                'angle_compensate': angle_compensate,
                'scan_mode': scan_mode
            }],
            output='screen'),
    ])


# 本launch文件用于启动物理Lidarbot机器人，树莓派摄像头v1.3，RPLIDAR A1，并集成ros2_control、twist_mux、robot_localization和手柄控制。
# 文件参考自 https://automaticaddison.com

import os

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch.event_handlers import OnProcessStart

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare



# 生成launch描述函数
def generate_launch_description():


    # 设置各个包和配置文件的路径
    pkg_path = FindPackageShare(package="lidarbot_bringup").find("lidarbot_bringup")
    pkg_description = FindPackageShare(package="lidarbot_description").find("lidarbot_description")
    pkg_teleop = FindPackageShare(package="lidarbot_teleop").find("lidarbot_teleop")
    pkg_navigation = FindPackageShare(package="lidarbot_navigation").find("lidarbot_navigation")

    controller_params_file = os.path.join(pkg_path, "config/controllers.yaml")  # ros2_control参数
    twist_mux_params_file = os.path.join(pkg_teleop, "config/twist_mux.yaml")   # twist_mux参数
    ekf_params_file = os.path.join(pkg_navigation, "config/ekf.yaml")           # EKF参数


    # 启动配置参数（可通过命令行传入）
    use_sim_time = LaunchConfiguration("use_sim_time")                # 是否使用仿真时间
    use_ros2_control = LaunchConfiguration("use_ros2_control")        # 是否启用ros2_control
    use_robot_localization = LaunchConfiguration("use_robot_localization")  # 是否启用定位包

    # 声明launch参数（可选项）
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name="use_sim_time",
        default_value="False",
        description="Use simulation (Gazebo) clock if true",
    )

    declare_use_ros2_control_cmd = DeclareLaunchArgument(
        name="use_ros2_control",
        default_value="True",
        description="Use ros2_control if true",
    )

    declare_use_robot_localization_cmd = DeclareLaunchArgument(
        name="use_robot_localization",
        default_value="True",
        description="Use robot_localization package if true",
    )

    # 启动 robot_state_publisher 节点，发布TF和URDF
    # 这里通过 IncludeLaunchDescription 嵌套调用 lidarbot_description 包下的 robot_state_publisher_launch.py
    # 这样可以实现launch文件的复用和参数传递
    start_robot_state_publisher_cmd = IncludeLaunchDescription(
        # 指定要包含的launch文件路径（Python格式）
        PythonLaunchDescriptionSource(
            [os.path.join(pkg_description, "launch", "robot_state_publisher_launch.py")]
        ),
        # 通过 launch_arguments 传递参数给被包含的launch文件
        launch_arguments={
            "use_sim_time": use_sim_time,           # 是否使用仿真时间，传递给下级launch
            "use_ros2_control": use_ros2_control,   # 是否启用ros2_control，传递给下级launch
        }.items(),
    )


    # 获取机器人URDF描述
    robot_description = Command([
        "ros2 param get --hide-type /robot_state_publisher robot_description"
    ])

    # 启动controller_manager（ros2_control主节点）
    start_controller_manager_cmd = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[{"robot_description": robot_description}, controller_params_file],
    )

    # 启动差速控制器
    start_diff_controller_cmd = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_controller", "--controller-manager", "/controller_manager"],
    )

    # 启动关节状态广播器
    start_joint_broadcaster_cmd = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broadcaster", "--controller-manager", "/controller_manager"],
    )

    # 启动IMU传感器广播器
    start_imu_broadcaster_cmd = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["imu_broadcaster", "--controller-manager", "/controller_manager"],
    )

    # 延迟2秒后启动controller_manager，确保robot_state_publisher已就绪
    start_delayed_controller_manager = TimerAction(
        period=2.0, actions=[start_controller_manager_cmd]
    )

    # controller_manager启动后再启动diff_controller
    start_delayed_diff_drive_spawner = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=start_controller_manager_cmd,
            on_start=[start_diff_controller_cmd],
        )
    )

    # controller_manager启动后再启动joint_broadcaster
    start_delayed_joint_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=start_controller_manager_cmd,
            on_start=[start_joint_broadcaster_cmd],
        )
    )

    # controller_manager启动后再启动imu_broadcaster
    start_delayed_imu_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=start_controller_manager_cmd,
            on_start=[start_imu_broadcaster_cmd],
        )
    )

    # 启动robot_localization包（EKF扩展卡尔曼滤波），用于融合定位
    start_robot_localization_cmd = Node(
        condition=IfCondition(use_robot_localization),
        package="robot_localization",
        executable="ekf_node",
        parameters=[
            ekf_params_file,
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
            ],
        remappings=[("/odometry/filtered", "/odom")],
    )

    # 启动手柄控制节点
    start_joystick_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [os.path.join(pkg_teleop, "launch", "joystick_launch.py")]
    ),
        launch_arguments={
            "use_sim_time": use_sim_time,
        }.items(),
    )
    
    # 启动RPLIDAR激光雷达节点
    start_rplidar_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [os.path.join(pkg_path, "launch", "rplidar_launch.py")]
        )
    )

    # 启动树莓派摄像头节点
    start_camera_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [os.path.join(pkg_path, "launch", "camera_launch.py")]
        )
    )

    # 启动twist_mux节点，实现多路速度指令切换
    start_twist_mux_cmd = Node(
        package="twist_mux",
        executable="twist_mux",populate

    # 创建LaunchDescription对象，依次添加所有动作
    ld = LaunchDescription()

    # 添加launch参数声明
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_use_ros2_control_cmd)
    ld.add_action(declare_use_robot_localization_cmd)

    # 添加各节点和动作
    ld.add_action(start_robot_state_publisher_cmd)
    ld.add_action(start_delayed_controller_manager)
    ld.add_action(start_delayed_diff_drive_spawner)
    ld.add_action(start_delayed_joint_broadcaster_spawner)
    ld.add_action(start_delayed_imu_broadcaster_spawner)
    ld.add_action(start_robot_localization_cmd)
    ld.add_action(start_joystick_cmd)
    ld.add_action(start_rplidar_cmd)
    ld.add_action(start_camera_cmd)
    ld.add_action(start_twist_mux_cmd)

    return ld

        parameters=[twist_mux_params_file],
        remappings=[("/cmd_vel_out", "/diff_controller/cmd_vel_unstamped")],
    )

    # Create the launch description and 
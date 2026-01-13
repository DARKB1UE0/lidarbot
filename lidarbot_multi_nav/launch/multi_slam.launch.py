#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

ROBOTS = ["robot1", "robot2", "robot3"]

def generate_launch_description():
    ld = LaunchDescription()

    # 1. 尝试寻找配置
    try:
        slam_pkg_share = FindPackageShare("slam_toolbox").find("slam_toolbox")
        default_config = os.path.join(slam_pkg_share, "config", "mapper_params_online_async.yaml")
    except:
        default_config = ""

    use_sim_time = LaunchConfiguration("use_sim_time")
    ld.add_action(DeclareLaunchArgument("use_sim_time", default_value="true"))

    slam_node_names = []

    # 2. 启动每个机器人的 SLAM 节点
    for robot in ROBOTS:
        node_name = 'slam_toolbox'
        # 修正点1：确保节点全名带上斜杠，防止 Lifecycle Manager 找不到
        full_node_name = f'/{robot}/{node_name}' 
        slam_node_names.append(full_node_name)

        slam_params = {
            'use_sim_time': use_sim_time,
            'base_frame': f'{robot}/base_link',
            'odom_frame': f'{robot}/odom',
            'map_frame': 'map', 
            'scan_topic': 'scan', # 在 namespace 下会自动变成 /robotX/scan
            'mode': 'mapping',
            'resolution': 0.01  # 设置为 0.02 (2cm) 以提高清晰度。默认是 0.05 (5cm)
        }

        node = Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name=node_name,
            namespace=robot,
            output='screen',
            parameters=[default_config, slam_params],
            # ==========================================================
            # 关键修复：TF 重映射
            # ==========================================================
            # 这里的第二个参数必须带斜杠 '/tf'，表示全局话题
            # 否则它会变成 /robot1/tf，RViz 就收不到数据了
            remappings=[
                ('/tf', '/tf'),
                ('/tf_static', '/tf_static'),
                ('/map', 'map') # 保持局部 map 话题 (/robot1/map)，避免多车冲突
            ]
        )
        ld.add_action(node)

    # ==========================================================
    # 3. 生命周期管理器
    # ==========================================================
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_slam',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'autostart': True},
            {'node_names': slam_node_names}
        ]
    )

    # 稍微增加一点延时，确保 SLAM 节点已经完全加载后再激活
    ld.add_action(TimerAction(period=5.0, actions=[lifecycle_manager]))

    return ld


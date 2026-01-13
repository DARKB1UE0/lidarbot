#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node 

def generate_launch_description():
    # 1. 获取包路径
    pkg_share = FindPackageShare("lidarbot_multi_nav").find("lidarbot_multi_nav")

    # 2. 定义 Launch 文件路径
    world_launch_path = os.path.join(pkg_share, "launch", "multi_world.launch.py")
    spawn_launch_path = os.path.join(pkg_share, "launch", "spawn_fleet.launch.py")
    slam_launch_path = os.path.join(pkg_share, "launch", "multi_slam.launch.py")
    nav_launch_path = os.path.join(pkg_share, "launch", "multi_nav.launch.py")

    # 3. 声明参数 (关键：这里的名字必须和你的 bash 脚本一致)
    # 你的脚本里用的是 start_slam:=true，所以这里必须叫 start_slam
    start_gazebo_arg = DeclareLaunchArgument(
        "start_gazebo", default_value="true", description="是否启动 Gazebo 环境"
    )
    start_slam_arg = DeclareLaunchArgument(
        "start_slam", default_value="false", description="是否启动 SLAM 建图"
    )
    start_nav_arg = DeclareLaunchArgument(
        "start_nav", default_value="false", description="是否启动导航"
    )
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time", default_value="true", description="使用仿真时间"
    )

    # 获取参数配置
    start_gazebo = LaunchConfiguration("start_gazebo")
    start_slam = LaunchConfiguration("start_slam")
    start_nav = LaunchConfiguration("start_nav")
    use_sim_time = LaunchConfiguration("use_sim_time")

    ld = LaunchDescription()

    # 添加参数声明
    ld.add_action(start_gazebo_arg)
    ld.add_action(start_slam_arg)
    ld.add_action(start_nav_arg)
    ld.add_action(use_sim_time_arg)

    # 4. 包含子 Launch 文件

    # A. 启动世界 (Gazebo) - 受 start_gazebo 控制
    # 你的脚本里设为了 false，因为你在脚本里手动启动了 Gazebo，这很好
    world_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(world_launch_path),
        condition=IfCondition(start_gazebo)
    )

    # B. 生成机器人 (Spawn Fleet) - 必须启动
    # 只要 demo_all 运行，就应该把车生成出来
    spawn_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(spawn_launch_path),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    # C. 启动 SLAM - 受 start_slam 控制
    slam_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(slam_launch_path),
        condition=IfCondition(start_slam),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )
    
    # ==========================================================
    # E. 【新增】地图合并节点 (Map Merge)
    # 只有在启动 SLAM 时才运行此节点
    # ==========================================================
    map_merge_node = Node(
        package='multirobot_map_merge',
        executable='map_merge',
        name='map_merge',
        condition=IfCondition(start_slam), # 只有建图时才合并
        parameters=[{
            'robot_map_topic': 'map',    # 侦测各机器人命名空间下的 map 话题
            'robot_namespace': '',       # 留空，让节点自动发现 robot1, robot2...
            'merged_map_topic': 'map',   # 输出的全局大地图话题名称
            'world_frame': 'world',      # 全局坐标系
            'known_init_poses': False,    # 仿真中我们知道初始位置，设为 True 提高精度
            'merging_rate': 2.0,         # 合并频率 (Hz)，太高会卡
            'discovery_rate': 0.5,       # 侦测新机器人的频率
            'use_sim_time': use_sim_time
        }],
        output='screen'
    )

    # D. 启动 Navigation - 受 start_nav 控制
    # 注意：通常 SLAM 和 Navigation 不会同时开，或者需要小心处理
    nav_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav_launch_path),
        condition=IfCondition(start_nav),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    # 添加动作
    ld.add_action(world_cmd)
    ld.add_action(spawn_cmd)
    ld.add_action(slam_cmd)
    ld.add_action(nav_cmd)

    return ld

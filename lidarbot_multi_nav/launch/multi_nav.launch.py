#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushRosNamespace
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource
from nav2_common.launch import RewrittenYaml

ROBOTS = ["robot1", "robot2", "robot3"]

def generate_launch_description():
    pkg_share = FindPackageShare("lidarbot_multi_nav").find("lidarbot_multi_nav")
    
    # 路径配置
    nav2_bringup_dir = FindPackageShare("nav2_bringup").find("nav2_bringup")
    nav_launch_file = os.path.join(nav2_bringup_dir, "launch", "bringup_launch.py")

    params_file = LaunchConfiguration(
        "params_file",
        default=os.path.join(pkg_share, "config", "nav2_params_override.yaml"),
    )
    default_map = os.path.join(pkg_share, "maps", "reference_map.yaml")
    map_file = LaunchConfiguration("map", default=default_map)
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    ld = LaunchDescription()

    # 声明参数
    ld.add_action(DeclareLaunchArgument("map", default_value=default_map))
    ld.add_action(DeclareLaunchArgument("params_file", default_value=params_file))
    ld.add_action(DeclareLaunchArgument("use_sim_time", default_value="true"))

    for robot in ROBOTS:
        # 使用 RewrittenYaml 自动处理参数中的命名空间
        param_substitutions = {
            'use_sim_time': use_sim_time,
            'yaml_filename': map_file
        }

        configured_params = RewrittenYaml(
            source_file=params_file,
            root_key=robot,
            param_rewrites=param_substitutions,
            convert_types=True
        )

        # 创建针对每个机器人的导航组
        nav_group = GroupAction([
            PushRosNamespace(robot),
            
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(nav_launch_file),
                launch_arguments={
                    'namespace': robot,
                    'use_namespace': 'True',
                    'map': map_file,
                    'use_sim_time': use_sim_time,
                    'params_file': configured_params,
                    'autostart': 'true',
                }.items(),
            )
        ])
        ld.add_action(nav_group)

    return ld

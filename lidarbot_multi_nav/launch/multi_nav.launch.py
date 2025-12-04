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
    params_file = LaunchConfiguration(
        "params_file",
        default=os.path.join(pkg_share, "config", "nav2_params_override.yaml"),
    )
    default_map = os.path.join(pkg_share, "maps", "reference_map.yaml")
    map_file = LaunchConfiguration("map", default=default_map)
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    ld = LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument(
            "params_file",
            default_value=os.path.join(pkg_share, "config", "nav2_params_override.yaml"),
        ),
        DeclareLaunchArgument("map", default_value=default_map),
    ])

    for robot in ROBOTS:
        robot_map_frame = f"{robot}/map"
        robot_odom_frame = f"{robot}/odom"
        robot_base_frame = f"{robot}/base_link"
        robot_scan_topic = f"/{robot}/scan"

        param_substitutions = {
            "use_sim_time": use_sim_time,
            "global_frame": robot_map_frame,
            "map_frame": robot_map_frame,
            "robot_base_frame": robot_base_frame,
            "base_frame_id": robot_base_frame,
            "odom_frame": robot_odom_frame,
            "odom_frame_id": robot_odom_frame,
            "scan_topic": robot_scan_topic,
            "yaml_filename": map_file,
        }

        configured_params = RewrittenYaml(
            source_file=params_file,
            root_key="",
            param_rewrites=param_substitutions,
            convert_types=True,
        )

        group = GroupAction([
            PushRosNamespace(robot),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(FindPackageShare("nav2_bringup").find("nav2_bringup"), "launch", "bringup_launch.py")
                ),
                launch_arguments={
                    "namespace": robot,
                    "use_sim_time": use_sim_time,
                    "map": map_file,
                    "params_file": configured_params,
                }.items(),
            ),
        ])
        ld.add_action(group)

    return ld

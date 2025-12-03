#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

ROBOTS = ["robot1", "robot2", "robot3"]


def generate_launch_description():
    pkg_share = FindPackageShare("lidarbot_multi_nav").find("lidarbot_multi_nav")
    default_params = os.path.join(pkg_share, "config", "slam_params.yaml")
    slam_params = LaunchConfiguration("slam_params", default=default_params)
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    ld = LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("slam_params", default_value=default_params),
    ])

    for robot in ROBOTS:
        robot_map_frame = f"{robot}/map"
        robot_odom_frame = f"{robot}/odom"
        robot_base_frame = f"{robot}/base_link"
        node = Node(
            package="slam_toolbox",
            executable="sync_slam_toolbox_node",
            name="slam_toolbox",
            namespace=robot,
            output="screen",
            parameters=[
                slam_params,
                {
                    "use_sim_time": use_sim_time,
                    "map_frame": robot_map_frame,
                    "odom_frame": robot_odom_frame,
                    "base_frame": robot_base_frame,
                    "scan_topic": "scan",
                },
            ],
            remappings=[("/scan", f"/{robot}/scan")],
        )
        ld.add_action(node)

    return ld

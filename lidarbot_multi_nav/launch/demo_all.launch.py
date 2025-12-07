#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare("lidarbot_multi_nav").find("lidarbot_multi_nav")

    start_gazebo = LaunchConfiguration("start_gazebo", default="true")
    start_slam = LaunchConfiguration("start_slam", default="false")

    multi_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_share, "launch", "multi_world.launch.py")),
        condition=IfCondition(start_gazebo),
    )

    spawn = TimerAction(
        period=3.0,
        actions=[IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(pkg_share, "launch", "spawn_fleet.launch.py")))]
    )

    slam = TimerAction(
        period=8.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(os.path.join(pkg_share, "launch", "multi_slam.launch.py")),
                condition=IfCondition(start_slam),
            )
        ]
    )

    nav = TimerAction(
        period=15.0,
        actions=[IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(pkg_share, "launch", "multi_nav.launch.py")))]
    )

    return LaunchDescription([
        DeclareLaunchArgument("start_gazebo", default_value="true"),
        DeclareLaunchArgument("start_slam", default_value="false"),
        multi_world,
        spawn,
        slam,
        nav,
    ])

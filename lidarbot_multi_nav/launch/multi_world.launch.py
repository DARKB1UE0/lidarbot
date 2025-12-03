#!/usr/bin/env python3
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_prefix
import os


def generate_launch_description():
    pkg_share = FindPackageShare("lidarbot_multi_nav").find("lidarbot_multi_nav")
    world_path = os.path.join(pkg_share, "worlds", "obstacle_arena.world")

    # Gazebo GUI crashes if HOME is missing; ensure we provide a sane fallback.
    default_home = os.environ.get("HOME") or os.path.expanduser("~")
    if not default_home:
        default_home = "/tmp/lidarbot_home"
    os.makedirs(default_home, exist_ok=True)

    existing_resource_path = os.environ.get("GAZEBO_RESOURCE_PATH", "")
    resource_segments = [pkg_share]
    if existing_resource_path:
        resource_segments.append(existing_resource_path)

    gazebo_ros_prefix = get_package_prefix("gazebo_ros")
    gazebo_ros_lib = os.path.join(gazebo_ros_prefix, "lib")
    existing_plugin_path = os.environ.get("GAZEBO_PLUGIN_PATH", "")
    plugin_segments = [gazebo_ros_lib, "/usr/lib/x86_64-linux-gnu/gazebo-11/plugins"]
    if existing_plugin_path:
        plugin_segments.append(existing_plugin_path)

    gazebo_env = {
        "GAZEBO_RESOURCE_PATH": os.pathsep.join(resource_segments),
        "GAZEBO_PLUGIN_PATH": os.pathsep.join(plugin_segments),
        "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH", ""),
        "HOME": default_home,
    }

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    gui = LaunchConfiguration("gui", default="true")

    gazebo_with_gui = ExecuteProcess(
        condition=IfCondition(gui),
        cmd=["gazebo", "--verbose", "-s", "libgazebo_ros_factory.so", world_path],
        output="screen",
        env=gazebo_env,
    )

    gazebo_headless = ExecuteProcess(
        condition=UnlessCondition(gui),
        cmd=["gzserver", "--verbose", "-s", "libgazebo_ros_factory.so", world_path],
        output="screen",
        env=gazebo_env,
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("gui", default_value="true"),
        gazebo_with_gui,
        gazebo_headless,
    ])

#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import LaunchConfiguration, Command

ROBOTS = [
    {"name": "robot1", "x": -2.0, "y": 0.0, "yaw": 0.0},
    {"name": "robot2", "x": 0.0, "y": -2.0, "yaw": 1.57},
    {"name": "robot3", "x": 2.0, "y": 0.0, "yaw": 3.14},
]


def generate_launch_description():
    description_pkg = FindPackageShare("lidarbot_description").find("lidarbot_description")
    robot_xacro = os.path.join(description_pkg, "urdf", "lidarbot.urdf.xacro")

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    actions = [DeclareLaunchArgument("use_sim_time", default_value="true")]

    for robot in ROBOTS:
        state_pub = Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            namespace=robot["name"],
            parameters=[
                {"use_sim_time": use_sim_time},
                {"frame_prefix": f"{robot['name']}/"},
                {
                    "robot_description": Command([
                        "xacro ",
                        robot_xacro,
                        " robot_name:=", robot["name"],
                        " use_ros2_control:=false",
                        " sim_mode:=true",
                    ])
                },
            ],
        )

        spawn = Node(
            package="gazebo_ros",
            executable="spawn_entity.py",
            arguments=[
                "-entity", robot["name"],
                "-topic", f"/{robot['name']}/robot_description",
                "-x", str(robot["x"]),
                "-y", str(robot["y"]),
                "-Y", str(robot["yaw"]),
            ],
        )

        # Add a delay to stagger the spawning of robots to reduce load on Gazebo
        # Robot 1: 0s delay, Robot 2: 20s delay, Robot 3: 40s delay
        delay_time = ROBOTS.index(robot) * 20.0
        
        if delay_time > 0:
            actions.append(state_pub)
            actions.append(TimerAction(period=delay_time, actions=[spawn]))
        else:
            actions.extend([state_pub, spawn])

    return LaunchDescription(actions)

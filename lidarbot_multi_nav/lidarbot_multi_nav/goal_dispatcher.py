import math
from typing import List

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.parameter import Parameter


ROBOT_NAMES: List[str] = ["robot1", "robot2", "robot3"]
TARGETS = {
    "robot1": [(1.5, 0.0, 0.0), (-1.5, 1.0, math.pi / 2.0)],
    "robot2": [(0.0, -1.5, 0.0), (1.0, 1.0, 0.0)],
    "robot3": [(-1.0, -1.0, 0.0), (2.0, 0.0, 0.0)],
}


def _make_pose(x: float, y: float, yaw: float, frame: str = "map") -> PoseStamped:
    pose = PoseStamped()
    pose.header.frame_id = frame
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.orientation.w = math.cos(yaw / 2.0)
    return pose


def send_goals():
    rclpy.init()
    navigators = {}
    for name in ROBOT_NAMES:
        navigator = BasicNavigator(namespace=name)
        navigator.node.set_parameters([Parameter("use_sim_time", Parameter.Type.BOOL, True)])
        navigator.waitUntilNav2Active()
        navigators[name] = navigator

    active = {name: 0 for name in ROBOT_NAMES}
    while rclpy.ok():
        for name, navigator in navigators.items():
            goals = TARGETS.get(name, [])
            if not goals:
                continue

            idx = active[name]
            if not navigator.isTaskActive():
                goal_pose = _make_pose(*goals[idx], frame=f"{name}/map")
                goal_pose.header.stamp = navigator.node.get_clock().now().to_msg()
                navigator.goToPose(goal_pose)
                active[name] = (idx + 1) % len(goals)
            else:
                result = navigator.getResult()
                if result in (TaskResult.SUCCEEDED, TaskResult.FAILED, TaskResult.CANCELED):
                    navigator.cancelTask()

        rclpy.spin_once(list(navigators.values())[0].node, timeout_sec=0.1)

    for navigator in navigators.values():
        navigator.lifecycleShutdown()
    rclpy.shutdown()


def main():
    try:
        send_goals()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

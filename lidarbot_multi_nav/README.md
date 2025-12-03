# lidarbot_multi_nav

多机器人导航包，提供 Gazebo 多机器人仿真场景、SLAM、Nav2 启动脚本以及简单的目标分发器。该 README 说明如何启动各组件、可实现的功能，以及关键节点之间的数据流。

## 功能概述

- **多机器人 Gazebo 场景**：`multi_world.launch.py` 加载 `worlds/obstacle_arena.world` 并生成仿真环境。
- **机器人生成**：`spawn_fleet.launch.py` 通过 `robot_state_publisher` 与 `gazebo_ros spawn_entity.py` 在不同 pose 下部署 `robot1~3`。
- **SLAM / 导航**：
  - `multi_slam.launch.py` 在每个命名空间运行 `slam_toolbox`，用于实时建图（可选）。
  - `multi_nav.launch.py` 基于 `nav2_bringup` 启动 Nav2 栈（AMCL、controller、planner 等），支持加载静态地图或消费 SLAM 输出。
- **一键流程**：`demo_all.launch.py` 通过 `TimerAction` 依次触发 world→spawn→slam→nav，实现完整仿真演示，可通过 `start_gazebo`、`start_slam` 控制阶段。
- **目标分发**：`lidarbot_multi_nav/goal_dispatcher.py` 使用 `nav2_simple_commander` 为每台机器人循环派发预设路径点。

## 启动方式

以下命令均需在构建完成后执行，并确保 `source install/setup.bash`。

1. **仅运行 Nav2（假设 gazebo/机器人已就绪）**
   ```bash
   ros2 launch lidarbot_multi_nav multi_nav.launch.py \
       use_sim_time:=true \
       map:=$HOME/dev_ws/install/lidarbot_multi_nav/share/lidarbot_multi_nav/maps/reference_map.yaml
   ```
   参数：
   - `use_sim_time`：默认 true。
   - `params_file`：可自定义 Nav2 参数 YAML。
   - `map`：静态地图路径；若使用 SLAM，可忽略并在 `multi_slam` 中发布地图。

2. **完整 demo（默认依次启动 world、spawn、nav）**
   ```bash
   ros2 launch lidarbot_multi_nav demo_all.launch.py \
       use_sim_time:=true \
       start_gazebo:=true \
       start_slam:=false
   ```
   - 将 `start_slam` 设为 `true` 可在 Nav2 之前启动 `multi_slam`。
   - 若已手动启动 Gazebo，可传 `start_gazebo:=false`。

3. **目标派发器**
   ```bash
   ros2 run lidarbot_multi_nav goal_dispatcher
   ```
   该脚本在 `robot1~3` 命名空间内创建 `BasicNavigator`，等待 Nav2 active 后依次发布 `TARGETS` 列表中的 `PoseStamped`。


## 目录速览

- `launch/`：各阶段启动脚本（world、spawn、slam、nav、demo）。
- `config/`：Nav2 参数 (`nav2_robot.yaml`)、SLAM 参数、行为树、RViz 配置。
- `maps/`：参考地图 (`reference_map.yaml/pgm`)。
- `worlds/`：Gazebo 场景。
- `scripts/`：入口脚本（goal_dispatcher）。

如需扩展机器人数量或改动路径点，可在 `launch/*.py` 中修改 `ROBOTS` 列表，在 `goal_dispatcher.py` 的 `TARGETS` 字典内添加目标。
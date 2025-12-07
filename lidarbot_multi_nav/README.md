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

## 常见问题与调试 (Troubleshooting)

### 1. 参数类型错误 (Invalid Type: Integer vs Double)
**现象**：
启动时报错 `parameter 'height' has invalid type: Wrong parameter type, parameter {height} is of type {integer}, setting it to {double} is not allowed.`

**原因**：
1.  Windows 与 Linux 换行符 (`CRLF` vs `LF`) 不兼容，导致 ROS 2 的 `RewrittenYaml` 工具解析失败，回退到默认的整数参数。
2.  配置文件中使用了整数（如 `20`）而非浮点数（如 `20.0`），导致类型推断错误。

**解决方案**：
1.  **强制修复换行符**：在虚拟机中运行以下命令，将所有源码文件转换为 Linux 格式：
    ```bash
    cd ~/dev_ws
    find src -type f \( -name "*.py" -o -name "*.yaml" -o -name "*.xml" -o -name "*.launch" -o -name "*.sh" \) -exec dos2unix {} +
    
    # 重新编译
    colcon build --symlink-install --packages-select lidarbot_multi_nav
    ```
2.  **使用浮点数**：在 YAML 文件中，确保 `height`, `width`, `loop_rate` 等参数使用带小数点的写法（如 `3.5`, `20.5`），避免使用 `.0` 结尾（有时会被误判），推荐使用 `.5` 等非零小数强制识别为 Double。

### 2. Gazebo 图形显示错误 (Can't open display)
**现象**：
报错 `[Err] [RenderEngine.cc:749] Can't open display:` 或 `Could not load the Qt platform plugin "xcb"`。

**原因**：
在 VS Code 终端或 SSH 远程终端中运行 Gazebo 时，无法连接到虚拟机的图形桌面环境。

**解决方案：分步启动法**
不要直接运行 `demo_all`，而是使用两个终端分别启动。

**终端 1：启动 Gazebo 环境**
```bash
# 1. 设置显示端口 (通常为 :0)
export DISPLAY=:0
# 2. 授予权限
xhost +
# 3. 手动启动 Gazebo 并加载世界
gazebo --verbose -s libgazebo_ros_factory.so install/lidarbot_multi_nav/share/lidarbot_multi_nav/worlds/obstacle_arena.world
```

**终端 2：启动机器人与导航**
等待 Gazebo 完全启动后：
```bash
# 1. 设置显示端口
export DISPLAY=:0
# 2. 启动剩余组件 (禁用 Gazebo 启动，但保留机器人生成和导航)
ros2 launch lidarbot_multi_nav demo_all.launch.py \
    use_sim_time:=true \
    start_gazebo:=false \
    start_slam:=false
```

### 3. Gazebo 卡死 / 显卡占用归零 (Resource Starvation)
**现象**：
启动 `demo_all.launch.py` 后，Gazebo 界面卡死，物理机显卡占用从 15% 掉到 0%。

**原因**：
同时启动 3 台机器人的导航栈（Nav2）会瞬间消耗大量 CPU 资源，导致 Gazebo 物理引擎线程饥饿（Starvation），仿真时钟停止，渲染线程挂起。

**解决方案：分级交错启动 (Staggered Launch) 与 物理引擎优化**
我们已经进一步优化了启动策略和仿真参数，以适应低性能虚拟机环境：

1.  **物理引擎降频**：将 Gazebo 物理更新频率从 1000Hz 降至 **250Hz** (`max_step_size` 0.004)。这能显著降低 CPU 负载。
2.  **传感器降级**：
    *   **Lidar**：频率降至 5Hz，采样点数降至 180。
    *   **Camera**：频率降至 1Hz，分辨率降至 320x240。
    *   **IMU**：已暂时禁用以节省资源。
3.  **增加超时时间**：在 `obstacle_arena.world` 中设置了 `model_plugin_loading_timeout` 为 120秒。
4.  **延长启动间隔**：
    *   机器人生成间隔延长至 **20秒**。
    *   导航启动推迟至 **60秒**。

**注意**：
请耐心等待启动过程，不要在所有节点完全启动前进行操作。整个启动过程大约需要 **2 分钟**。

### 3. 传感器初始化超时 (Sensors failed to initialize)
**现象**：
Gazebo 报错 `Sensors failed to initialize when loading model[robot2]...`。

**原因**：
同时生成多个机器人导致 CPU 负载过高，仿真器来不及初始化传感器插件。

**解决方案**：
已在 `spawn_fleet.launch.py` 中实现了**错峰生成**逻辑：
- Robot 1: 立即生成
- Robot 2: 延时 5 秒
- Robot 3: 延时 10 秒
- `maps/`：参考地图 (`reference_map.yaml/pgm`)。
- `worlds/`：Gazebo 场景。
- `scripts/`：入口脚本（goal_dispatcher）。

如需扩展机器人数量或改动路径点，可在 `launch/*.py` 中修改 `ROBOTS` 列表，在 `goal_dispatcher.py` 的 `TARGETS` 字典内添加目标。
# Nav2 多机器人 Debug Log

**日期**: 2025-12-04  
**相关包**: `lidarbot_multi_nav`, `lidarbot_navigation`

## 现象
- 启动 `ros2 launch lidarbot_multi_nav multi_nav.launch.py` 时，`controller_server`、`planner_server`、`waypoint_follower` 等生命周期节点在 `configuring` 阶段报错：
  - `Parameter {height, width, loop_rate} has incorrect type: expected double, got integer`。
- `/tmp/launch_params_*` 中的参数已经显示为浮点型，但错误仍旧出现。

## 排查过程
1. 检查运行时生成的 `/tmp/launch_params_*`，确认 `robot2`/`robot3` 的 `height`、`width`、`loop_rate` 均为浮点数。
2. 进一步搜索仓库中 Nav2 相关 YAML：
   - `lidarbot_multi_nav/config/nav2_robot.yaml` 已经全部使用浮点数。
   - `lidarbot_navigation/config/nav2_params.yaml` 仍存在 `width: 3`、`height: 3`、`loop_rate: 20` 等整数。
3. 推测当 `RewrittenYaml` 失败或容器回落到 `nav2_params.yaml` 时，整数类型被加载并导致 Nav2 节点拒绝启动。

## 根因
- `lidarbot_navigation/config/nav2_params.yaml` 的局部参数文件仍包含整数，且存在被 `nav2_bringup` 兜底加载的可能，触发 Nav2 的强类型检查。

## 解决方案
1. 将 `lidarbot_navigation/config/nav2_params.yaml` 中的相关字段改成浮点数：
   ```diff
-      width: 3
-      height: 3
+      width: 3.0
+      height: 3.0
@@
-    loop_rate: 20
+    loop_rate: 20.0
   ```
2. 重新编译并安装：
   ```bash
   cd ~/dev_ws
   rm -rf build install log
   colcon build --symlink-install
   source install/setup.bash
   ```
3. 再次启动 multi-nav，确认前 30~40 行日志中显示的 `params_file` 路径及 `/tmp/launch_params_*` 均为最新文件。
4. 在每次重启前确认无残留 `component_container_isolated` 进程，必要时清理旧的 `/tmp/launch_params_*`。

## 后续建议
- 在所有 Nav2 参数模板中保持数值型字段为浮点格式，避免类型回退问题。
- 为 launch 文件增加显式的 `params_file` 绝对路径（或 `ament_index_cpp` 查找结果）验证，防止使用到默认模板。
- 每次提交前运行 `grep -n "loop_rate: [0-9]\+$" -R lidarbot_*` 之类的检查，确保不会再引入只含整数的 Nav2 参数。

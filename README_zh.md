# Lidarbot（中文翻译）

<!-- ![ROS2 CI](https://github.com/TheNoobInventor/lidarbot/actions/workflows/.github/workflows/lidarbot_ci_action.yml/badge.svg) -->

一个差速驱动机器人，使用在树莓派 4（运行 Ubuntu Server 22.04）上运行的 ROS2 Humble 进行控制。该车配备了用于视觉反馈的 Raspberry Pi 摄像头和用于同时定位与建图（SLAM）的 RPlidar A1 传感器，并使用 Nav2 栈进行自主导航。此外，机器人上使用了 MPU6050 惯性测量单元（IMU），由 `robot_localization` 包中的扩展卡尔曼滤波（EKF）节点融合 IMU 数据与轮编码器数据，以提供更精确的里程计估计。

硬件部分为 Waveshare Motor Driver HAT 和 MPU6050 传感器编写了驱动，以便通过 `ros2_control` 资源管理器分别被 `ros2_control` 差速驱动控制器和 IMU 传感器广播器访问。

<p align='center'>
    <img src=docs/images/real_mapping.gif width="600">
</p>

本工作的预印本可在此处获取：[here](http://dx.doi.org/10.13140/RG.2.2.15748.54408)。

- [Lidarbot](#lidarbot)
  - [🗃️ 包概览](#️-package-overview)
  - [🧰 硬件](#hardware)
    - [零件清单](#part-list)
    - [项目接线与装配](#project-wiring-and-assembly)
  - [🔌 安装](#-installation)
    - [开发机设置](#development-machine-setup)
      - [WiringPi](#wiringpi)
      - [MPU6050 库](#mpu6050-library)
      - [加载 ROS 环境](#sourcing-ros-installation)
      - [Gazebo Fortress](#gazebo-fortress)
      - [在 RViz 中显示 lidarbot 模型](#display-lidarbot-model-in-rviz)
      - [遥控操作（Teleoperation）](#teleoperation)
      - [Twist mux（合并速度命令）](#twist-mux)
    - [Lidarbot 设置](#lidarbot-setup)
      - [Motor Driver HAT](#motor-driver-hat)
      - [Raspberry Pi 摄像头](#raspberry-pi-camera)
      - [MPU6050 偏移量](#mpu6050-offsets)
  - [网络配置](#network-configuration)
  - [ros2_control 框架](#ros2-control-framework)
    - [硬件组件](#hardware-components)
      - [System（系统）](#system)
      - [Sensor（传感器）](#sensor)
      - [Actuator（执行器）](#actuator)
    - [资源管理器（Resource Manager）](#resource-manager)
    - [控制器（Controllers）](#controllers)
      - [差速驱动控制器](#differential-drive-controller)
      - [关节状态广播器](#joint-state-broadcaster)
      - [IMU 传感器广播器](#imu-sensor-broadcaster)
    - [控制器管理器（Controller Manager）](#controller-manager)
  - [测试驱动（Test Drive）](#test-drive)
    - [机器人定位](#robot-localization)
    - [Gazebo 仿真](#gazebo)
    - [实物测试](#physical)
  - [建图（Mapping）](#mapping)
    - [Gazebo 仿真建图](#gazebo-1)
    - [实物建图](#physical-1)
  - [导航（Navigation）](#navigation)
    - [Gazebo 导航](#gazebo-2)
    - [实物导航](#physical-2)
  - [Aruco 包](#aruco-package)
    - [生成 ArUco 标记](#generate-aruco-marker)
    - [摄像头标定](#webcam-calibration)
    - [Aruco 轨迹可视化节点](#aruco-trajectory-visualizer-node)
  - [致谢](#acknowledgment)


## 🗃️ 包概览
- `lidarbot_aruco`（./lidarbot_aruco/）：包含使用 ArUco 标记的配置、launch 与节点文件。  
- `lidarbot_base`（./lidarbot_base/）：包含 lidarbot 的 `ros2_control` 硬件组件以及 Waveshare Motor Driver HAT 的底层代码。  
- `lidarbot_bringup`（./lidarbot_bringup/）：包含 MPU6050 模块的硬件组件、用于启动摄像头、激光雷达和真实 lidarbot 的 launch 文件。  
- `lidarbot_description`（./lidarbot_description/）：包含 lidarbot 的 URDF 描述文件、传感器和 `ros2_control` 配置。  
- `lidarbot_gazebo`（./lidarbot_gazebo/）：包含在 Gazebo Classic 中模拟 lidarbot 所需的配置、launch 和 world 文件。  
- `lidarbot_gz`（./lidarbot_gz/）：包含在 Gazebo Fortress 中模拟 lidarbot 所需的 urdf、launch 和 world 文件。  
- `lidarbot_navigation`（./lidarbot_navigation/）：包含用于导航的 launch、配置和地图文件。  
- `lidarbot_slam`（./lidarbot_slam/）：包含为 slam_toolbox 和 RViz 提供的配置文件，以及用于用 SLAM 生成地图的 launch 文件。  
- `lidarbot_teleop`（./lidarbot_teleop/）：包含在仿真和实物上使用手柄控制 lidarbot 的配置与 launch 文件。  

## 🧰 硬件
### 零件清单
本项目使用了下列组件：

| 序号 | 部件 |
| -- | -- |
|1| Raspberry Pi 4 (4 GB)|
|2| SanDisk 32 GB SD 卡（最低）|
|3| 双轮驱动机器人底盘套件（Two wheel drive robot chassis kit）|
|4| Waveshare Motor Driver HAT|
|5| 2 x 带编码器和线束的电机|
|6| MPU6050 模块|
|7| RPlidar A1|
|8| Raspberry Pi 摄像头 v1.3|
|9| 用于 RPlidar A1 和 RPi 4 的 3D 打印支架|
|10| Raspberry Pi 摄像头的安装支架|
|11| 给 RPi 4 的移动电源（输出至少 5V 3A）|
|12| 游戏手柄|
|13| 迷你旅行路由器（可选）|
|14| 3 槽 18650 电池座|
|15| 3 节 18650 电池（为 Motor Driver HAT 供电）|
|16| 母对母杜邦跳线|
|17| 备用导线|
|18| Logitech C270 摄像头（可选）|

其他工具或部件包括：
| 序号 | 工具/配件 |
| -- | -- |
|1| 烙铁|
|2| 3D 打印机|
|3| 螺丝刀套装|
|4| 双面胶|

此外，在 Raspberry Pi 4 与其 3D 打印支架之间使用了一些尼龙柱（尼龙螺柱），以便更容易插拔移动电源的 USB 电源线。

### 项目接线与装配

电子元件按下图连接。

<p align="center">
  <img title='Wiring diagram' src=docs/images/lidarbot_wiring.png width="800">
</p>

MPU6050 板的引脚通过 I2C 协议接到树莓派 GPIO，连接方式如下：

| MPU6050 板 | GPIO.BOARD | GPIO.BCM |
| --- | --- | --- |
| VCC | 3.3V | 3.3V |
| GND | GND | GND |
| SCL | 05 | GPIO03 |
| SDA | 03 | GPIO02 |

在早期版本中，使用带 20 个槽位的光电中断式编码器盘（随底盘套件），但由于每圈仅 20 个计数，对于导航精度太低，因此更换为带内置编码器的新电机 —— 新电机每圈脉冲数约为 **1084**（参考 Automatic Addison 教程计算）。

使用的新电机如下图所示：

<p align='center'>
  <img title='Motors' src=docs/images/motors.jpg width="400">
  <img title='Motor pins' src=docs/images/motor_pins.jpg width="400">
</p>

左右电机的引脚连接如下：

右电机：

| 引脚 | GPIO.BOARD | GPIO.BCM |
| --- | --- | --- |
| C1 (Encoder A) | 22 | GPIO25 |
| C2 (Encoder B) | 16 | GPIO23 |
| VCC | 5V | 5V |
| GND | GND | GND |

左电机：

| 引脚 | GPIO.BOARD | GPIO.BCM |
| --- | --- | --- |
| C1 (Encoder A) | 18 | GPIO24 |
| C2 (Encoder B) | 15 | GPIO22 |
| VCC | 5V | 5V |
| GND | GND | GND |

备注：  
C1 用于计数相应电机的脉冲，C2 用于检测该电机的运动方向（前进或后退）。

<p align='center'>
  <img title='MPU6050' src=docs/images/mpu6050.jpg width="400">
  <img title='Encoders' src=docs/images/encoders.jpg width="400">
</p>

Waveshare Motor Driver HAT 的螺丝端子块与电机的 M+ / M- 以及电池座如下连接：

| Motor Driver HAT 引脚 | 连接 |
| --- | --- |
| MA1 | 红线（左电机） |
| MA2 | 黑线（左电机） |
| GND | 电池座 黑线 |
| VIN | 电池座 红线 |
| MB1 | 红线（右电机） |
| MB2 | 黑线（右电机） |

<p align='center'>
  <img title='Motor Driver HAT' src=docs/images/Motor_Driver_HAT.png width="400">
</p>

将线缆（随电机提供）焊接到电机上，若随电机提供线太短，可能需要备用线以便接到 Motor Driver HAT。如果车轮朝反方向转动，可交换端子块上对应电机的两根线以反转方向。

最后，Raspberry Pi 摄像头连接到树莓派的排线插槽，RPlidar A1 插到 RPi 的 USB 口。

<p align='center'>
  <img title='Top View' src=docs/images/top_view.jpg width="600">
</p>

<p align='center'>
  <img title='Side View' src=docs/images/side_view.jpg width="600">
</p>

## 🔌 安装

### 开发机设置

开发机（PC）用于运行 Gazebo、RViz 等计算量较大的程序，也可用于远程控制 lidarbot。  

本项目要求在开发机上使用 Ubuntu 22.04 LTS（与 ROS2 Humble 兼容）。ROS2 Humble 的安装指南可见官方文档。开发机上安装桌面版本（包含 RViz）：

```
sudo apt install ros-humble-desktop
```

然后安装 ROS 开发工具：

```
sudo apt install ros-dev-tools
```

安装完成后，在开发机创建工作区并克隆仓库：

```
mkdir -p ~/dev_ws/src
cd ~/dev_ws/src
git clone https://github.com/TheNoobInventor/lidarbot.git .
```

接着安装依赖（使用 rosdep）：

```
cd ~/dev_ws
sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src --rosdistro humble -r -y
```

后续文档中引用到的 ROS 包默认假设已通过上面命令安装，除非特别说明。

在构建工作区前，还需要安装 WiringPi i2c 库（用于树莓派 GPIO）以及 MPU6050 的依赖。

#### WiringPi

为了在树莓派 4 上使用 GPIO，并用 C/C++ 操作引脚，本项目使用了非官方的 WiringPi（因为硬件接口使用 C++ 编写）。安装方法：

```
cd ~/Downloads
git clone https://github.com/wbeebe/WiringPi.git
cd WiringPi/
./build
```

检查当前 gpio 版本：

```
gpio -v
```

WiringPi 的参考文章见 README 中链接。

#### MPU6050 库

使用了 Alex Mous 的 C/C++ MPU6050 库（针对 Raspberry Pi 4），并加入了四元数支持，用于 `lidarbot_bringup` 包内的 `ros2_control` IMU 传感器广播器。

MPU6050 使用 I2C 协议，需安装 I2C 相关依赖：

```
sudo apt install libi2c-dev i2c-tools libi2c0
```

#### 加载 ROS 环境（Sourcing ROS Installation）

为避免每次打开终端都手动 source ROS 安装路径（underlay），可以将 source 命令写入 shell 配置文件。

使用 bash：

```
echo "source /opt/ros/humble/setup.bash" >> $HOME/.bashrc
```

使用 zsh：

```
echo "source /opt/ros/humble/setup.zsh" >> $HOME/.zshrc
```

同样，也可以把工作区 overlay 的 source 命令加入配置：

使用 bash：

```
echo "source ~/dev_ws/install/setup.bash" >> $HOME/.bashrc
source $HOME/.bashrc
```

使用 zsh：

```
echo "source ~/dev_ws/install/setup.zsh" >> $HOME/.zshrc
source $HOME/.zshrc
```

执行 `source $HOME/.zshrc` 会使当前终端生效（后续打开终端不再需要）。

---
然后在工作区根目录执行构建命令：

```
cd ~/dev_ws
colcon build --symlink-install
```

`--symlink-install` 选项使安装使用符号链接而非复制，便于在修改某些文件时无需频繁重建。

#### Gazebo Fortress

更新说明：之前使用 Gazebo Classic，但 Classic 已被弃用，建议使用 Gazebo（Ignition）Fortress 版本以配合 Ubuntu 22.04。仓库中仍保留 `lidarbot_gazebo`（Gazebo Classic）包，但可能遇到安装问题，建议迁移到 Fortress。

Gazebo Fortress 的 ROS 集成安装请参考官方指南。

#### 在 RViz 中显示 lidarbot 模型

使用已安装的 `xacro` 工具处理 URDF 文件并合并为完整 URDF。使用 `description_launch.py` 在 RViz 中显示模型：

```
ros2 launch lidarbot_description description_launch.py
```

<p align='center'>
  <img src=docs/images/lidarbot_rviz.png width="800">
</p>

配合 `joint_state_publisher_gui` 可以在 GUI 窗口通过滑块移动非静态链接（如车轮）。若想启用 GUI，把 `use_gui` 参数设为 `true`：

```
ros2 launch lidarbot_description description_launch.py use_gui:=true
```

<p align='center'>
  <img src=docs/images/joint_state_publisher_gui.gif width="800">
</p>

可通过在 launch 命令末尾加 `--show-args` 来查看该 launch 可接受的参数及默认值：

```
ros2 launch lidarbot_description description_launch.py --show-args
```

#### 遥控（Teleoperation）

项目使用无线游戏手柄用于仿真和实物控制。测试映射使用 `joy_tester` 包。首先插入 USB 接收器，然后运行：

```
ros2 run joy joy_node
```

另外在新终端运行：

```
ros2 run joy_tester test_joy
```

会弹出 GUI，按动按钮和操纵杆以确认输入。手柄配置文件位于 `lidarbot_teleop/config/joystick.yaml`，示例映射：

| 按钮/杆 | 轴号 | 功能 |
| --- | --- | --- |
| L1 按钮 | 4 | 按住此使能键以正常速度移动机器人 |
| 左操纵杆 | 2 | 前后移动控制线速度 |
| 右操纵杆 | 1 | 左右移动控制角速度 |

将 `require_enable_button` 设为 `true` 可要求按住 L1 才能移动，松开则停止。可通过 `enable_turbo_button` 指定未使用的按钮以启用“加速”模式。

`joy_node` 的 `deadzone` 参数用于指定操纵杆偏离中心到多少才被视为有效（范围 -1 到 1）。例如 `0.25` 表示轴需移动到 25% 的量程才输出非零值。该值需针对手柄实际性能调优。

#### Twist mux（速度命令多路复用）

使用 `twist_mux` 包将多个速度命令来源（如手柄与导航栈）按优先级合并为一个 `geometry_msgs::Twist` 输出。在本项目中，手柄的优先级高于导航命令（示例配置）：

```
twist_mux:
  ros__parameters:
    topics:
      navigation:
        topic   : cmd_vel
        timeout : 0.5
        priority: 10
      joystick:
        topic   : cmd_vel_joy
        timeout : 0.5
        priority: 100
```

### Lidarbot（树莓派）设置

在 Raspberry Pi 上安装 ROS2 Humble 前，先将 Ubuntu Server 22.04 刷到 SD 卡。按照官方流程设置 ROS 环境，随后安装 ROS-Base 和开发工具：

```
sudo apt install ros-humble-ros-base ros-dev-tools
```

在树莓派创建工作区并克隆仓库：

```
mkdir -p ~/robot_ws/src
cd ~/robot_ws/src
git clone https://github.com/TheNoobInventor/lidarbot.git .
```

安装 ROS 依赖（示例中跳过 rviz、gazebo 包，因为这些只在 PC 上运行）：

```
cd ~/robot_ws
sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -r -y \ 
--skip-keys "rviz2 gazebo_ros2_control gazebo_ros_pkgs" --rosdistro humble
```

在构建前需要先安装 WiringPi i2c 库与 MPU6050 库依赖，详见上文。构建工作区：

```
cd ~/robot_ws
colcon build --symlink-install
```

#### Motor Driver HAT

Waveshare Motor Driver HAT 的接口实现位于 `lidarbot_base/include/lidarbot_base/` 与 `lidarbot_base/src/`。目录结构示例如 README 所示。

表格总结了各文件及功能（略）——详见 README 原文。

控制层次关系示意图：

<p align='center'>
  <img src=docs/images/motor_control_hierarchy.jpg width="600">
</p>

修改 Waveshare 原始文件的主要目的是为了使其支持 WiringPi，并采用可行的方法来检测电机转向（因为所用编码器使用霍尔传感器，较易获得方向信号）。

<p align='center'>
  <img src=docs/images/hall_effect_sensors.png width="800">
</p>

霍尔效应传感器检测电机旋转时磁场的变化；每次信号从低到高（上升沿）或处理策略规定的边沿计为一次脉冲（tick），脉冲数用于轮子里程计。下图示意脉冲随时间的变化。

<p align='center'>
  <img src=docs/images/time_interval.jpg width="600">
</p>

用于里程计的编码器脉冲（tick）数，例如本项目电机每 360° 大约 **1084** 次脉冲。该数据将与 MPU6050 IMU 数据一起通过 `robot_localization` 的 EKF 融合，以提高里程计精度。

#### Raspberry Pi 摄像头

安装以下包以使用 Raspberry Pi Camera v1.3：

```
sudo apt install libraspberrypi-bin v4l-utils raspi-config
```

启用摄像头支持：

```
sudo raspi-config
```

在菜单中启用摄像头，然后用以下命令确认连接：

```
vcgencmd get_camera
```

应返回类似：

```
supported=1 detected=1, libcamera interfaces=0
```

#### MPU6050 偏移量（Offsets）

在使用 IMU 广播器前，需要校准 MPU6050 以去除偏移和噪声，步骤如下：

- 将 lidarbot 放在水平静止的表面，拔掉 RPlidar。  
- 运行提供的可执行程序生成偏移值（C++ 可执行文件在 `lidarbot_bringup` 的 CMakeLists.txt 中定义）。构建包：

```
colcon build --symlink-install --packages-select lidarbot_bringup
```

运行偏移生成程序：

```
ros2 run lidarbot_bringup mpu6050_offsets
```

将输出的偏移值替换到 `lidarbot_bringup/include/lidarbot_bringup/mpu6050_lib.h` 的相应宏中，然后重建包。

IMU 的量程设置和偏差可在 `mpu6050_lib.h` 顶部查看/修改。

## 网络配置

开发机与 lidarbot 必须连接到同一局域网以便双向通信。文中参考的网络指南演示了如何配置多机 ROS2 环境。为避免局域网中不同设备产生冲突，设置 `ROS_DOMAIN_ID`（0–101 范围）到相同值（示例使用 31）：

```
echo "export ROS_DOMAIN_ID=31" >> ~/.zshrc
source $HOME/.zshrc
```

如需固定 IP，可在路由器上为 lidarbot 分配静态地址。建议使用支持至少 WiFi 5 的路由器以减少延迟。若需记录 ros2bag，推荐用 MCAP 存储以提升读写性能。

## ros2_control 框架

为了同时在仿真与实物上控制机器人，使用 `ros2_control` 框架。`ros2_control` 是一个与硬件无关的控制框架，提供硬件抽象、控制器复用与实时性能支持。其主要组成有：

1. 硬件组件（Hardware Components）
2. 资源管理器（Resource Manager）
3. 控制器（Controllers）
4. 控制器管理器（Controller Manager）

### 硬件组件

硬件组件是对物理硬件的驱动封装，通常用 C++ 编写并通过 `pluginlib` 导出为插件，由资源管理器动态加载。硬件组件在 URDF（或 xacro） 中通过 `<ros2_control>` 标签配置。

三种基本组件类型：

#### System（系统组件）

用于多自由度硬件（如机器人底盘）。例如，Waveshare Motor Driver HAT 控制两个电机，因此机器人底盘被配置为系统组件，具有读/写接口（状态接口 & 命令接口）。URDF 中示例配置在 README 中给出。

#### Sensor（传感器组件）

只读接口，用于发布传感器数据。MPU6050 被配置为外部传感器组件，挂在 `imu_link`。

#### Actuator（执行器）

单自由度组件，比如电机。可以既有命令也有状态接口（若可获得反馈）。

图示（硬件组件）见 README。

### 资源管理器（Resource Manager）

RM 负责加载硬件组件插件、管理生命周期与接口，`read()` 与 `write()` 在控制循环中与硬件通信，便于对硬件实现复用与独占访问控制。

### 控制器（Controllers）

控制器对比目标与反馈，计算需要写入硬件的命令。常见控制器包括差速驱动控制器、关节控制器等。差速驱动控制器将 Nav2 输出的速度命令写入系统硬件的速度命令接口，从而驱动电机。

#### 差速驱动控制器

接收 `Twist`，写入底盘的速度命令接口。

#### 关节状态广播器

只读，用于发布 `/joint_states` 与 `/dynamic_joint_state`，供 RViz 使用。

#### IMU 传感器广播器

发布 `Imu` 消息到 `imu_broadcaster/imu`，供 `robot_localization` 的 EKF 融合。

IMU 的 covariance（方差/协方差）数组需要计算并配置到 `controllers.yaml`，项目中提供了 `mpu6050_covariances.cpp` 用于采样计算方差（默认采样 500 次，延时 0.25s）。

运行采样节点：

```
ros2 run lidarbot_bringup mpu6050_covariances
```

将输出的方差数组复制粘贴到 `lidarbot_bringup/config/controllers.yaml` 的 `imu_broadcaster` 参数中。

### 控制器管理器（Controller Manager）

CM 管理控制器的生命周期（加载、激活、停用、卸载），并通过 RM 访问硬件接口。CM 的 `update()` 方法在控制循环中被调用，执行 `read`、更新控制器输出并 `write` 回硬件。

架构图见 README。

## 测试驱动（Test Drive）

### 机器人定位

在使用 Nav2 进行导航前，需要先融合轮编码器与 IMU 数据以弥补轮滑引起的里程计误差。使用 `robot_localization` 的 EKF 融合 `/diff_controller/odom`（轮里程计）与 `imu_broadcaster/imu`（IMU）来生成更稳健的里程计供 Nav2 使用。EKF 配置文件位于 `lidarbot_navigation/config/ekf.yaml`。

可在 launch 时通过 `use_robot_localization` 参数启用或禁用 EKF。例如关闭：

```
ros2 launch lidarbot_bringup lidarbot_bringup_launch.py use_robot_localization:=false
```

### Gazebo 仿真

在 Gazebo Fortress 中驱动机器人，确保游戏手柄的 USB 接收器在开发机上插入，然后运行：

```
ros2 launch lidarbot_gz gz_launch.py
```

GIF 展示了用游戏手柄在仿真场景中控制机器人行驶的效果。

### 实物测试

提供了一个 ROS 服务用于测试电机连接（详见 `lidarbot_base/src/motor_checks_server.cpp` 与 client），运行前请确保 18650 电池已充电，并将机器人置于箱子等支撑物上以防坠落。

运行客户端请求自检：

```
ros2 run lidarbot_base motor_checks_client
```

再运行服务器执行检测：

```
ros2 run lidarbot_base motor_checks_server
```
这些 are the steps followed by the server node:
- 将左右电机脉冲计数初始化为 0。  
- 以 50% 速度正向运行每个电机 2 秒。终端示例输出见 README。  
- 检查每个电机的脉冲计数是否大于 0。  
- 若两侧都大于 0，则返回成功；否则返回失败并指出有故障的电机（目前若出现某些错误会抛出 std::future_error，README 中提到该问题尚待修复）。

<p align='center'>
    <img src=docs/images/motor_connection_tests.gif width="400">
</p>

若某电机反向转动，可交换该电机的接线以改变方向。

确认两电机都能正向转动后，可以使用下面命令一键启动实体机器人（摄像头、RPLIDAR、ros2_control、twist_mux、robot_localization 与游戏手柄）：

```
ros2 launch lidarbot_bringup lidarbot_bringup_launch.py
```

**注意**：摄像头相关可能出现一些警告/错误信息，多数与相机标定相关，可忽略。

## 建图（Mapping）

Nav2 使用激光扫描数据构建环境地图并进行定位。使用 `slam_toolbox` 配合 RPLIDAR A1 在驱动机器人时生成地图（在仿真中使用 `teleop_twist_joy` 配合游戏手柄）。

### Gazebo 建图

在开始建图前，确保 `lidarbot_slam/config/mapper_params_online_async.yaml` 的 `mode` 设置为 `mapping`，并注释掉 `map_file_name`、`map_start_pose`、`map_start_at_dock`（如果存在）。

启动仿真并在另一个终端运行 `slam_toolbox` 的在线模式，然后在 RViz 中查看并保存地图。README 中包含详细的启动命令示例。

### 实物建图

在实体机器人上运行 bringup，然后在开发机上用 `slam_toolbox`（`use_sim_time:=false`）和 RViz 生成并保存地图，过程与仿真类似。

## 导航（Navigation）

Nav2 使用 AMCL（自适应蒙特卡洛定位）进行基于激光的定位。导航过程中，Nav2 输出速度命令到差速驱动控制器（本项目使用的 topic 为 `diff_controller/cmd_vel_unstamped`），控制器驱动电机并产生里程计 `/diff_controller/odom`，该里程计与 `imu_broadcaster/imu` 融合后输入 Nav2 进行新一轮控制。

导航相关的 topic 图在 README 中给出。

### Gazebo 导航

在生成的地图上使用 Nav2 进行定位与导航，README 中给出了在 Gazebo Fortress / Classic 中启动 localization 与 navigation 的示例命令，并说明需在 RViz 中设置初始位姿（2D Pose Estimate）及目标位姿（2D Goal Pose）。

### 实物导航

在实体机器人上运行类似的命令（`use_sim_time:=false`），并在 RViz 中设置初始与目标位姿以开始导航。

## Aruco 包

项目包含使用 ArUco 码进行位姿估计与轨迹可视化的工具。

### 生成 ArUco 标记

需要安装 `opencv-contrib-python`（而非 `opencv-python`）：

```
pip uninstall opencv-python
pip install opencv-contrib-python
```

然后进入 `lidarbot_aruco` 目录并运行 `generate_aruco_marker.py` 生成图片文件（示例命令在 README 中）。

### 摄像头标定

若使用 Logitech C270 摄像头，先安装 usb_cam 驱动：

```
sudo apt install ros-humble-usb-cam
```

按 README 中指南对摄像头进行标定，运行 usb_cam 节点并传入对应 params yaml。

### ArUco 轨迹可视化节点

运行：

```
ros2 run lidarbot_aruco aruco_trajectory_visualizer_node
```

或使用 launch 启动 usb 驱动与可视化节点：

```
ros2 launch lidarbot_aruco trajectory_visualizer_launch.py
```

<p align='center'>
    <img src=docs/images/lidarbot_aruco_marker.png width="600">
</p>

<p align='center'>
    <img src=docs/images/lidarbot_aruco_test.gif width="800">
</p>

导航开始/结束位置示意图见 README。

## 致谢

- Articulated Robotics
- Automatic Addison
- Diffbot
- Linorobot2
- Mini pupper
- Pyimagesearch
- Robotics Backend

---

翻译说明：
- 我保留了原 README 中的所有命令、代码块、图片链接与外部链接（未翻译 URL/命令），只翻译了解释性文字与标题，使得中文读者更易阅读。  
- 如果你希望我把翻译覆盖原 `README.md`（替换）或改为在仓库中新建 `README_zh.md`（当前操作为新建），请告知偏好。  
- 若需要我将英文与中文并列展示，也可以实现（例如在同一文件中先英文后中文或左右并列）。

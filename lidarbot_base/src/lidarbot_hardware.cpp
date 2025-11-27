#include "lidarbot_base/lidarbot_hardware.hpp"

namespace lidarbot_base
{
//日志记录器
LidarbotHardware::LidarbotHardware()
    : logger_(rclcpp::get_logger("LidarbotHardware"))
{}
//初始化函数，返回成功或错误
CallbackReturn LidarbotHardware::on_init(const hardware_interface::HardwareInfo & info)//引用传递硬件参数
{
    if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS)
    {
        return CallbackReturn::ERROR;
    }

    RCLCPP_INFO(logger_, "正在初始化..");

    config_.left_wheel_name = info_.hardware_parameters["left_wheel_name"];
    config_.right_wheel_name = info_.hardware_parameters["right_wheel_name"];
    config_.enc_ticks_per_rev = std::stoi(info_.hardware_parameters["enc_ticks_per_rev"]);
    config_.loop_rate = std::stod(info_.hardware_parameters["loop_rate"]);

    //配置左右轮
    left_wheel_.setup(config_.left_wheel_name, config_.enc_ticks_per_rev);
    right_wheel_.setup(config_.right_wheel_name, config_.enc_ticks_per_rev);

    RCLCPP_INFO(logger_, "初始化完成");

    return CallbackReturn::SUCCESS;
}

// 导出机器人各轮子的状态接口（如速度、位置），供控制器读取
std::vector<hardware_interface::StateInterface> LidarbotHardware::export_state_interfaces()
{
    // 为每个轮子设置速度和位置的状态接口

    std::vector<hardware_interface::StateInterface> state_interfaces;

    // 左轮速度接口
    state_interfaces.emplace_back(hardware_interface::StateInterface(left_wheel_.name, hardware_interface::HW_IF_VELOCITY, &left_wheel_.velocity));//接口名称，接口类型，实际数据
    // 左轮位置接口
    state_interfaces.emplace_back(hardware_interface::StateInterface(left_wheel_.name, hardware_interface::HW_IF_POSITION, &left_wheel_.position));
    // 右轮速度接口
    state_interfaces.emplace_back(hardware_interface::StateInterface(right_wheel_.name, hardware_interface::HW_IF_VELOCITY, &right_wheel_.velocity));
    // 右轮位置接口
    state_interfaces.emplace_back(hardware_interface::StateInterface(right_wheel_.name, hardware_interface::HW_IF_POSITION, &right_wheel_.position));

    // 返回所有状态接口
    return state_interfaces;
}

// 导出机器人各轮子的控制接口（如速度命令），供控制器下发指令
std::vector<hardware_interface::CommandInterface> LidarbotHardware::export_command_interfaces()
{
    // 为每个轮子设置速度命令接口

    std::vector<hardware_interface::CommandInterface> command_interfaces;

    // 左轮速度命令接口
    command_interfaces.emplace_back(hardware_interface::CommandInterface(left_wheel_.name, hardware_interface::HW_IF_VELOCITY, &left_wheel_.command));
    // 右轮速度命令接口
    command_interfaces.emplace_back(hardware_interface::CommandInterface(right_wheel_.name, hardware_interface::HW_IF_VELOCITY, &right_wheel_.command));

    // 返回所有命令接口
    return command_interfaces;
}

// 配置机器人硬件（电机和编码器），初始化相关引脚和中断
CallbackReturn LidarbotHardware::on_configure(const rclcpp_lifecycle::State & /*previous_state*/)// 不需要使用上个状态的信息，注释掉参数名，仅保留类型，表示未使用该参数
{
    RCLCPP_INFO(logger_, "配置电机和编码器.."); // 输出配置开始日志

    // 初始化电机驱动
    Motor_Init();

    // 初始化 wiringPi，使用 BCM GPIO 编号
    wiringPiSetupGpio();
    
    // 设置编码器中断引脚和方向引脚为输入模式
    pinMode(LEFT_WHL_ENC_INT, INPUT);   // 左轮编码器中断引脚
    pinMode(RIGHT_WHL_ENC_INT, INPUT);  // 右轮编码器中断引脚
    pinMode(LEFT_WHL_ENC_DIR, INPUT);   // 左轮编码器方向引脚
    pinMode(RIGHT_WHL_ENC_DIR, INPUT);  // 右轮编码器方向引脚

    // 给编码器中断引脚上拉电阻，防止悬空
    pullUpDnControl(LEFT_WHL_ENC_INT, PUD_UP);
    pullUpDnControl(RIGHT_WHL_ENC_INT, PUD_UP);

    // 初始化编码器中断，下降沿触发，分别绑定左右轮的脉冲处理函数
    wiringPiISR(LEFT_WHL_ENC_INT, INT_EDGE_FALLING, left_wheel_pulse);
    wiringPiISR(RIGHT_WHL_ENC_INT, INT_EDGE_FALLING, right_wheel_pulse);

    RCLCPP_INFO(logger_, "成功配置电机和编码器"); // 输出配置完成日志

    return CallbackReturn::SUCCESS;
}

// 启动/关闭控制器时输出日志
CallbackReturn LidarbotHardware::on_activate(const rclcpp_lifecycle::State & /*previous_state*/)
{
    RCLCPP_INFO(logger_, "正在启动控制器..");

    return CallbackReturn::SUCCESS;
}

CallbackReturn LidarbotHardware::on_deactivate(const rclcpp_lifecycle::State & /*previous_state*/)
{   
    RCLCPP_INFO(logger_, "正在关闭控制器..");

    return CallbackReturn::SUCCESS;
}

// 读取硬件状态（如轮子编码器），并计算轮子的位姿和速度
return_type LidarbotHardware::read(const rclcpp::Time & /*time*/, const rclcpp::Duration & period)
{
    // 获取本周期经过的时间（秒）
    double delta_seconds = period.seconds();

    // 读取左右轮编码器的当前计数值
    read_encoder_values(&left_wheel_.encoder_ticks, &right_wheel_.encoder_ticks);

    // 计算左轮的位姿和速度
    double previous_position = left_wheel_.position; // 记录上一次的位姿
    left_wheel_.position = left_wheel_.calculate_encoder_angle(); // 根据编码器计数计算当前位姿
    left_wheel_.velocity = (left_wheel_.position - previous_position) / delta_seconds; // 计算速度

    // 计算右轮的位姿和速度
    previous_position = right_wheel_.position;
    right_wheel_.position = right_wheel_.calculate_encoder_angle();
    right_wheel_.velocity = (right_wheel_.position - previous_position) / delta_seconds;

    // 返回读取成功
    return return_type::OK;
}

// 将控制器下发的速度命令转换为电机驱动指令并发送到硬件
return_type LidarbotHardware::write(const rclcpp::Time & /*time*/, const rclcpp::Duration & period)
{   
    // 计算本周期内左轮应输出的电机脉冲数
    double left_motor_counts_per_loop = left_wheel_.command / left_wheel_.rads_per_tick / config_.loop_rate;
    // 计算本周期内右轮应输出的电机脉冲数
    double right_motor_counts_per_loop = right_wheel_.command / right_wheel_.rads_per_tick / config_.loop_rate;

    // 发送速度指令到电机驱动器
    set_motor_speeds(left_motor_counts_per_loop, right_motor_counts_per_loop);

    // 返回写入成功
    return return_type::OK;
}

} // namespace lidarbot_base

// 引入 pluginlib 宏定义头文件，用于插件导出
#include "pluginlib/class_list_macros.hpp"

// 导出插件：将 LidarbotHardware 注册为 hardware_interface::SystemInterface 插件
// 这样 ROS2 控制框架可以通过插件机制动态加载本硬件类
PLUGINLIB_EXPORT_CLASS(
    lidarbot_base::LidarbotHardware, 
    hardware_interface::SystemInterface)

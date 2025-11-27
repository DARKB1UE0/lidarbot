// ROS 2 节点：订阅 Twist 指令并调用底层电机驱动，实现手柄控制小车

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "lidarbot_base/motor_encoder.h"

#include <chrono>
#include <csignal>
#include <functional>
#include <string>

using namespace std::chrono_literals;

namespace
{
// 夹紧工具函数，避免对 C++17 std::clamp 的依赖
inline double clamp_value(double value, double min_value, double max_value)
{
    if (value < min_value)
    {
        return min_value;
    }
    if (value > max_value)
    {
        return max_value;
    }
    return value;
}

void initialize_motor_interface()
{
    static bool initialized = false;
    if (initialized)
    {
        return;
    }

    // 初始化电机驱动与编码器 GPIO
    Motor_Init();
    wiringPiSetupGpio();

    pinMode(LEFT_WHL_ENC_INT, INPUT);
    pinMode(RIGHT_WHL_ENC_INT, INPUT);
    pinMode(LEFT_WHL_ENC_DIR, INPUT);
    pinMode(RIGHT_WHL_ENC_DIR, INPUT);

    pullUpDnControl(LEFT_WHL_ENC_INT, PUD_UP);
    pullUpDnControl(RIGHT_WHL_ENC_INT, PUD_UP);

    wiringPiISR(LEFT_WHL_ENC_INT, INT_EDGE_FALLING, left_wheel_pulse);
    wiringPiISR(RIGHT_WHL_ENC_INT, INT_EDGE_FALLING, right_wheel_pulse);

    signal(SIGINT, handler);
    initialized = true;
}
} // namespace

class JoystickDriveNode : public rclcpp::Node
{
public:
    JoystickDriveNode()
        : Node("joystick_drive_node"), motors_stopped_(true)
    {
        cmd_vel_topic_ = declare_parameter<std::string>("cmd_vel_topic", "/cmd_vel_joy");
        max_linear_velocity_ = declare_parameter<double>("max_linear_velocity", 0.4);
        max_angular_velocity_ = declare_parameter<double>("max_angular_velocity", 1.0);
        turning_gain_ = declare_parameter<double>("turning_gain", 1.0);
        max_pwm_percent_ = declare_parameter<double>("max_pwm_percent", 80.0);
        command_timeout_sec_ = declare_parameter<double>("command_timeout", 0.5);

        initialize_motor_interface();
        last_command_time_ = this->get_clock()->now();

        cmd_vel_sub_ = create_subscription<geometry_msgs::msg::Twist>(
            cmd_vel_topic_, rclcpp::QoS{10},
            std::bind(&JoystickDriveNode::twist_callback, this, std::placeholders::_1));

        watchdog_timer_ = create_wall_timer(
            100ms, std::bind(&JoystickDriveNode::watchdog_callback, this));

        RCLCPP_INFO(get_logger(), "Joystick drive node ready. Waiting for Twist messages on %s", cmd_vel_topic_.c_str());
    }

    ~JoystickDriveNode() override
    {
        set_motor_speeds(0.0, 0.0);
        Motor_Stop(MOTORA);
        Motor_Stop(MOTORB);
    }

private:
    void twist_callback(const geometry_msgs::msg::Twist::SharedPtr msg)
    {
        if (!msg)
        {
            return;
        }

        const double linear_norm = (max_linear_velocity_ > 0.0)
                                       ? clamp_value(msg->linear.x / max_linear_velocity_, -1.0, 1.0)
                                       : 0.0;
        const double angular_norm = (max_angular_velocity_ > 0.0)
                                        ? clamp_value(msg->angular.z / max_angular_velocity_, -1.0, 1.0)
                                        : 0.0;

        const double linear_component = linear_norm * max_pwm_percent_;
        const double angular_component = angular_norm * turning_gain_ * max_pwm_percent_;

        const double left_command = clamp_value(linear_component - angular_component, -max_pwm_percent_, max_pwm_percent_);
        const double right_command = clamp_value(linear_component + angular_component, -max_pwm_percent_, max_pwm_percent_);

        set_motor_speeds(left_command, right_command);

        last_command_time_ = this->get_clock()->now();
        motors_stopped_ = false;
    }

    void watchdog_callback()
    {
        const auto now = this->get_clock()->now();
        const double elapsed = (now - last_command_time_).seconds();

        if (elapsed > command_timeout_sec_ && !motors_stopped_)
        {
            set_motor_speeds(0.0, 0.0);
            motors_stopped_ = true;
            RCLCPP_WARN(get_logger(), "No Twist command received for %.2f s. Stopping motors.", elapsed);
        }
    }

    std::string cmd_vel_topic_;
    double max_linear_velocity_;
    double max_angular_velocity_;
    double turning_gain_;
    double max_pwm_percent_;
    double command_timeout_sec_;

    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_sub_;
    rclcpp::TimerBase::SharedPtr watchdog_timer_;

    rclcpp::Time last_command_time_;
    bool motors_stopped_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<JoystickDriveNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}


// 服务器节点：运行电机自检，通过让两个电机前进来确认电机工作是否正常


#include "rclcpp/rclcpp.hpp"              // ROS2 C++主库
#include "std_srvs/srv/trigger.hpp"       // 标准空请求/响应服务
#include "lidarbot_base/motor_encoder.h"  // 电机编码器相关定义


// 重置编码器脉冲计数器
void reset_pulse_counters()
{
    right_wheel_pulse_count = 0; // 右轮脉冲数清零
    left_wheel_pulse_count = 0;  // 左轮脉冲数清零
}


// 让指定电机前进，检测编码器脉冲数判断电机是否正常
// motor_id: MOTORA(0)为左电机，MOTORB(1)为右电机
bool move_motor(int motor_id)
{   
    reset_pulse_counters(); // 先清零脉冲计数
    sleep(2);               // 等待2秒，确保计数器已清零
    
    // 以50%速度让电机前进2秒
    Motor_Run(motor_id, FORWARD, 50);
    sleep(2);
    Motor_Stop(motor_id);   // 停止电机

    // 检查脉冲数是否大于0，判断电机是否真的转动
    if (motor_id == MOTORA) {
        if (left_wheel_pulse_count > 0) {
            return true;    // 左电机正常
        } else return false; // 左电机异常
    }
    if (motor_id == MOTORB) {
        if (right_wheel_pulse_count > 0) {
            return true;    // 右电机正常
        } return false;     // 右电机异常
    }
}


// 服务回调函数：收到客户端请求后，依次检测左右电机
void checkMotors(const std::shared_ptr<std_srvs::srv::Trigger::Request> request, 
                std::shared_ptr<std_srvs::srv::Trigger::Response> response) {
    // 初始化响应内容
    response->success = true;
    response->message = "";
    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "收到电机自检请求...");

    // 检查左电机
    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "正在检测左电机...");
    auto left_motor_passed = move_motor(MOTORA);
    if (!left_motor_passed) {
        response->success = false;
        response->message += "左电机检测失败，请检查电机接线。";
    }

    // 检查右电机
    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "正在检测右电机...");
    auto right_motor_passed = move_motor(MOTORB);
    if (!right_motor_passed) {
        response->success = false;
        response->message += "右电机检测失败，请检查电机接线。";
    }

    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "自检结果已返回客户端...");
}


int main(int argc, char **argv)
{
    // 初始化电机驱动
    Motor_Init();

    // 初始化wiringPi，采用BCM引脚编号
    wiringPiSetupGpio();
    
    // 设置编码器中断和方向引脚为输入模式
    pinMode(LEFT_WHL_ENC_INT, INPUT);
    pinMode(RIGHT_WHL_ENC_INT, INPUT);
    pinMode(LEFT_WHL_ENC_DIR, INPUT);
    pinMode(RIGHT_WHL_ENC_DIR, INPUT);

    // 给编码器引脚上拉，防止悬空
    pullUpDnControl(LEFT_WHL_ENC_INT, PUD_UP);
    pullUpDnControl(RIGHT_WHL_ENC_INT, PUD_UP);

    // 初始化编码器中断，下降沿触发，分别绑定左右轮脉冲处理函数
    wiringPiISR(LEFT_WHL_ENC_INT, INT_EDGE_FALLING, left_wheel_pulse);
    wiringPiISR(RIGHT_WHL_ENC_INT, INT_EDGE_FALLING, right_wheel_pulse);

    // 初始化rclcpp库
    rclcpp::init(argc, argv);

    // 创建一个名为"motor_checks_server"的节点
    std::shared_ptr<rclcpp::Node> node = rclcpp::Node::make_shared("motor_checks_server");

    // 创建名为"checks"的服务，回调函数为checkMotors
    rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr service = 
        node->create_service<std_srvs::srv::Trigger>("checks", &checkMotors);

    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "电机自检服务已就绪");

    // 循环运行节点，直到被终止
    rclcpp::spin(node);
    rclcpp::shutdown();
}

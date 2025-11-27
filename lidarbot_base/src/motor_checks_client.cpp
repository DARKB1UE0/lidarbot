
// 客户端节点，请求执行电机自检服务


#include "rclcpp/rclcpp.hpp"              // ROS2 C++主库
#include "std_srvs/srv/trigger.hpp"       // 标准空请求/响应服务


// 用于表示时间长度的C++命名空间
using namespace std::chrono_literals;


int main(int argc, char **argv) {// char **argv等效char* argv[]，字符串指针数组
    // 初始化 rclcpp 库
    rclcpp::init(argc, argv);

    // 创建一个名为 "motor_checks_client" 的节点
    std::shared_ptr<rclcpp::Node> node = rclcpp::Node::make_shared("motor_checks_client");

    // 创建一个客户端，准备请求名为 "checks" 的服务（服务类型为 Trigger）
    rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr client = 
        node->create_client<std_srvs::srv::Trigger>("checks");

    // 创建一个空的请求对象
    auto request = std::make_shared<std_srvs::srv::Trigger::Request>();

    // 循环等待服务端上线（每2秒检查一次）
    while (!client->wait_for_service(2s)) {
        // 如果ROS被关闭，则报错并退出
        if (!rclcpp::ok()) {
            RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "等待服务时被中断，退出.");
            return 0;
        }
        // 服务还未上线，提示用户继续等待
        RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "服务未就绪，继续等待...");
    }

    // 发送异步请求到服务端
    auto result = client->async_send_request(request);

    // 等待服务端返回结果
    if (rclcpp::spin_until_future_complete(node, result) == rclcpp::FutureReturnCode::SUCCESS) {
        // 检查返回结果的 success 字段，判断自检是否通过
        if (result.get()->success) {
            RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "电机自检通过！");
        } else {
            // 输出自检失败的详细信息
            RCLCPP_WARN(rclcpp::get_logger("rclcpp"), "电机自检未通过: %s", result.get()->message.c_str());
        }
    } else {
        RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "调用服务 'checks' 失败");
    }

    // 关闭 rclcpp，释放资源
    rclcpp::shutdown();
    return 0;
}

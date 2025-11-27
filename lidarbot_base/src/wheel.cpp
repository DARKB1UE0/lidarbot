#include "lidarbot_base/wheel.hpp"

Wheel::Wheel(const std::string &wheel_name, int ticks_per_rev)
{
    setup(wheel_name, ticks_per_rev);
}

// 设置轮子参数：名称和每个编码器脉冲对应的弧度
void Wheel::setup(const std::string &wheel_name, int ticks_per_rev)
{
    name = wheel_name; // 设置轮子的名称
    rads_per_tick = (2*M_PI)/ticks_per_rev; // 计算每个编码器脉冲对应的弧度值
}

double Wheel::calculate_encoder_angle()
{
    return encoder_ticks * rads_per_tick;
}

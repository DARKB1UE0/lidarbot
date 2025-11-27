
// 本文件用于计算编码器脉冲数，并根据接收到的指令设置每个电机的运行速度
// 适配 Waveshare 电机驱动板硬件

#include "lidarbot_base/motor_encoder.h"
#include <math.h>


// 左右轮编码器脉冲计数器
int left_wheel_pulse_count = 0;
int right_wheel_pulse_count = 0;


// 轮子方向变量，1 表示前进，0 表示后退
int left_wheel_direction = 1;
int right_wheel_direction = 1;


// 读取当前左右轮编码器脉冲数
void read_encoder_values(int *left_encoder_value, int *right_encoder_value) {
  *left_encoder_value = left_wheel_pulse_count;
  *right_encoder_value = right_wheel_pulse_count;
}


// 左轮编码器中断回调函数
void left_wheel_pulse() {
  // 读取左轮方向（1-前进，0-后退）
  left_wheel_direction = digitalRead(LEFT_WHL_ENC_DIR);

  // 根据方向累加或递减脉冲数
  if (left_wheel_direction == 1)
    left_wheel_pulse_count++;
  else
    left_wheel_pulse_count--;
}


// 右轮编码器中断回调函数
void right_wheel_pulse() {
  // 读取右轮方向（1-前进，0-后退）
  right_wheel_direction = digitalRead(RIGHT_WHL_ENC_DIR);

  // 根据方向累加或递减脉冲数
  if (right_wheel_direction == 1)
    right_wheel_pulse_count++;
  else
    right_wheel_pulse_count--;
}


// 根据速度指令设置左右电机的转速和方向
void set_motor_speeds(double left_wheel_command, double right_wheel_command) {
  // 电机方向枚举变量
  DIR left_motor_direction;
  DIR right_motor_direction;

  // 通过系数调整电机速度，系数与编码器脉冲数有关，根据实际调整系数

  double left_motor_speed = ceil(left_wheel_command * 1.65);
  double right_motor_speed = ceil(right_wheel_command * 1.65);

  // 判断速度正负，设置电机方向
  if (left_motor_speed > 0)
    left_motor_direction = FORWARD;
  else
    left_motor_direction = BACKWARD;

  if (right_motor_speed > 0)
    right_motor_direction = FORWARD;
  else
    right_motor_direction = BACKWARD;

  // 按指定方向和速度运行电机
  Motor_Run(MOTORA, left_motor_direction, (int)abs(left_motor_speed));
  Motor_Run(MOTORB, right_motor_direction, (int)abs(right_motor_speed));
}


// 信号处理函数，收到终止信号时停止电机
void handler(int signo) {
  Motor_Stop(MOTORA);
  Motor_Stop(MOTORB);
  exit(0);
}

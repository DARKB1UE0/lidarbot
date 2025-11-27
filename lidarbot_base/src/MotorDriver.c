#include "lidarbot_base/MotorDriver.h"
#include "lidarbot_base/Debug.h"

/*****************************************************************************
* | 文件名      :   MotorDriver.c
* | 作者        :   Waveshare 团队
* | 功能        :   驱动 TB6612FNG 电机驱动芯片
* | 说明        :
*                TB6612FNG 是一种低导通电阻的直流电机驱动芯片。
*                通过 IN1 和 IN2 两个输入信号，可实现正转、反转、刹车和停止等模式。
* | 版本        :   V1.0
* | 日期        :   2018-09-04
* | 备注        :   基础版本
******************************************************************************/
#include "lidarbot_base/MotorDriver.h"
#include "lidarbot_base/Debug.h"


// 记录A、B两路电机的IN1/IN2引脚电平状态
UWORD ain1_value, ain2_value; 
UWORD bin1_value, bin2_value;


/**
 * 电机驱动初始化
 *
 * 主要初始化PWM控制芯片PCA9685，并设置PWM频率
 *
 * 示例：
 * Motor_Init();
 */
void Motor_Init(void)
{
    PCA9685_Init(0x40);        // 初始化PCA9685，I2C地址0x40
    PCA9685_SetPWMFreq(50);    // 设置PWM频率为50Hz
}

/**

/**
 * 控制电机转动
 *
 * @param motor: MOTORA 或 MOTORB，选择A/B路电机
 * @param dir: FORWARD（前进）或 BACKWARD（后退）
 * @param speed: 转速（0~100）
 *
 * 示例：
 * Motor_Run(MOTORA, FORWARD, 50);
 * Motor_Run(MOTORB, BACKWARD, 100);
 */
void Motor_Run(UBYTE motor, DIR dir, UWORD speed)
{
    if(speed > 100)
        speed = 100; // 限制最大速度为100

    if(motor == MOTORA) {
        DEBUG("Motor A Speed = %d\r\n", speed);
        PCA9685_SetPwmDutyCycle(PWMA, speed); // 设置A路PWM占空比
        if(dir == FORWARD) {
            DEBUG("forward...\r\n");
            PCA9685_SetLevel(AIN1, 0); // AIN1=0,AIN2=1为前进
            PCA9685_SetLevel(AIN2, 1);
            ain1_value = 0;
            ain2_value = 1;
        } else {
            DEBUG("backward...\r\n");
            PCA9685_SetLevel(AIN1, 1); // AIN1=1,AIN2=0为后退
            PCA9685_SetLevel(AIN2, 0);
            ain1_value = 1;
            ain2_value = 0;
        }
    } else {
        DEBUG("Motor B Speed = %d\r\n", speed);
        PCA9685_SetPwmDutyCycle(PWMB, speed); // 设置B路PWM占空比
        if(dir == FORWARD) {
            DEBUG("forward...\r\n");
            PCA9685_SetLevel(BIN1, 0); // BIN1=0,BIN2=1为前进
            PCA9685_SetLevel(BIN2, 1);
            bin1_value = 0;
            bin2_value = 1;
        } else {
            DEBUG("backward...\r\n");
            PCA9685_SetLevel(BIN1, 1); // BIN1=1,BIN2=0为后退
            PCA9685_SetLevel(BIN2, 0);
            bin1_value = 1;
            bin2_value = 0;
        }
    }
}


/**
 * 停止指定电机
 *
 * @param motor: MOTORA 或 MOTORB
 *
 * 示例：
 * Motor_Stop(MOTORA);
 */
void Motor_Stop(UBYTE motor)
{
    if(motor == MOTORA) {
        PCA9685_SetPwmDutyCycle(PWMA, 0); // A路PWM占空比设为0，停止
    } else {
        PCA9685_SetPwmDutyCycle(PWMB, 0); // B路PWM占空比设为0，停止
    }
}


/**
 * 获取指定电机当前方向
 *   1 - 前进
 *   0 - 后退
 *
 * @param motor: MOTORA 或 MOTORB
 *
 * 示例：
 * Motor_Direction(MOTORA);
 */
UBYTE Motor_Direction(UBYTE motor)
{
    if(motor == MOTORA) {
        if(ain1_value == 0 && ain2_value == 1)
            return 1; // 前进
        else if(ain1_value == 1 && ain2_value == 0)
            return 0; // 后退
    }
    else {
        if(bin1_value == 0 && bin2_value == 1)
            return 1; // 前进
        else if(bin1_value == 1 && bin2_value == 0)
            return 0; // 后退
    }
}

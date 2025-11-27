
# 本launch文件用于启动树莓派摄像头v1.3，运行v4l2_camera节点

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

	# 创建LaunchDescription对象，包含一个摄像头节点
	return LaunchDescription([
		Node(
			package='v4l2_camera',              # 节点所属包名
			executable='v4l2_camera_node',       # 可执行文件名
			output='screen',                     # 输出到终端
			namespace='camera',                  # 命名空间为camera
			parameters=[{                        # 节点参数
				'image_size': [640, 480],        # 图像分辨率 640x480
				'time_per_frame': [1, 6],        # 每帧时间（1/6秒，约6fps）
				'camera_frame_id': 'camera_link_optical' # 相机TF坐标系id
				}]
			)
		])

from setuptools import setup

package_name = 'lidarbot_multi_nav'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', [
            'launch/multi_world.launch.py',
            'launch/spawn_fleet.launch.py',
            'launch/multi_slam.launch.py',
            'launch/multi_nav.launch.py',
            'launch/demo_all.launch.py',
        ]),
        ('share/' + package_name + '/config', [
            'config/slam_params.yaml',
            'config/nav2_robot.yaml',
            'config/nav2_params_override.yaml',
            'config/behavior_tree.xml',
            'config/rviz_multi.rviz',
        ]),
        ('share/' + package_name + '/worlds', ['worlds/obstacle_arena.world']),
        ('share/' + package_name + '/maps', ['maps/reference_map.yaml', 'maps/reference_map.pgm']),
        ('share/' + package_name + '/scripts', ['scripts/goal_dispatcher.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=False,
    maintainer='lidarbot developer',
    maintainer_email='you@example.com',
    description='Launch files and utilities for multi-robot mapping and navigation with lidarbot.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'goal_dispatcher = lidarbot_multi_nav.goal_dispatcher:main',
        ],
    },
)

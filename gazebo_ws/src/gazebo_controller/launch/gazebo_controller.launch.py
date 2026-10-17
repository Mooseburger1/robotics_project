import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


# Matching URDF description of vehicle_blue so RViz2 renders the 3D robot on the chassis frame
VEHICLE_BLUE_URDF = """<?xml version="1.0"?>
<robot name="vehicle_blue">
  <material name="blue"><color rgba="0.0 0.0 1.0 1.0"/></material>
  <material name="red"><color rgba="1.0 0.0 0.0 1.0"/></material>
  <material name="green"><color rgba="0.0 1.0 0.0 1.0"/></material>

  <link name="chassis">
    <visual>
      <geometry><box size="2.0 1.0 0.5"/></geometry>
      <material name="blue"/>
    </visual>
  </link>

  <link name="left_wheel">
    <visual>
      <geometry><cylinder radius="0.4" length="0.2"/></geometry>
      <material name="red"/>
    </visual>
  </link>

  <link name="right_wheel">
    <visual>
      <geometry><cylinder radius="0.4" length="0.2"/></geometry>
      <material name="red"/>
    </visual>
  </link>

  <link name="caster">
    <visual>
      <geometry><sphere radius="0.2"/></geometry>
      <material name="green"/>
    </visual>
  </link>

  <joint name="left_wheel_joint" type="continuous">
    <parent link="chassis"/>
    <child link="left_wheel"/>
    <origin xyz="-0.5 0.6 0.0" rpy="-1.5707 0.0 0.0"/>
    <axis xyz="0 0 1"/>
  </joint>

  <joint name="right_wheel_joint" type="continuous">
    <parent link="chassis"/>
    <child link="right_wheel"/>
    <origin xyz="-0.5 -0.6 0.0" rpy="-1.5707 0.0 0.0"/>
    <axis xyz="0 0 1"/>
  </joint>

  <joint name="caster_wheel" type="fixed">
    <parent link="chassis"/>
    <child link="caster"/>
    <origin xyz="0.8 0.0 -0.2" rpy="0.0 0.0 0.0"/>
  </joint>
</robot>
"""


def generate_launch_description():
    pkg_share = get_package_share_directory('gazebo_controller')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    sdf_file = os.path.join(pkg_share, 'worlds', 'maze_robot.sdf')

    # 1. Launch Gazebo Sim with the maze_robot.sdf world (-r starts unpaused)
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {sdf_file}'}.items(),
    )

    # 2. Launch the ROS 2 <-> Gazebo parameter_bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        output='screen',
    )

    # 3. Launch robot_state_publisher so the 3D robot model is visible in RViz2
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': VEHICLE_BLUE_URDF}],
        output='screen',
    )

    # 4. Launch the DiffDrive PID Controller Node
    pid_controller = Node(
        package='gazebo_controller',
        executable='diffdrive_pid',
        name='diffdrive_pid',
        output='screen',
    )

    return LaunchDescription([
        gz_sim,
        bridge,
        robot_state_publisher,
        pid_controller,
    ])
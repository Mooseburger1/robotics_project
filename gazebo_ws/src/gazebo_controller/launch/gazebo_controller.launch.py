import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node




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
    <axis xyz="0 0 1"/>
  </joint>
</robot>
"""




def generate_launch_description():
    pkg_share = get_package_share_directory('gazebo_controller')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')


    sdf_file = os.path.join(pkg_share, 'worlds', 'maze_robot.sdf')
    rviz_config_file = os.path.join(pkg_share, 'rviz', 'rviz.rviz')


    # Launch Gazebo Sim (-r starts unpaused)
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {sdf_file}'}.items(),
    )


    # Launch ROS 2 <-> Gazebo parameter_bridge
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


    # Launch robot_state_publisher (with frame_prefix 'vehicle_blue/' to match rviz.rviz)
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{
            'robot_description': VEHICLE_BLUE_URDF,
            'frame_prefix': 'vehicle_blue/',
        }],
        output='screen',
    )


    # Launch the DiffDrive PID Controller Node
    pid_controller = Node(
        package='gazebo_controller',
        executable='diffdrive_pid',
        name='diffdrive_pid',
        output='screen',
    )


    # Launch RViz2 with the saved rviz/rviz.rviz configuration
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        output='screen',
    )


    # Launch rqt_reconfigure GUI for live PD slider tuning
    rqt_reconfigure_node = Node(
        package='rqt_reconfigure',
        executable='rqt_reconfigure',
        name='rqt_reconfigure',
        output='screen',
    )


    # Launch teleop_twist_keyboard in its own pop-up xterm window
    # We are also remmaping the /cm_vel to /teleop_cmd_vel so we can gracefully handle
    # any race conditions between 2d goal pose from rviz and any commands from teleop keyboard
    teleop_node = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        prefix='xterm -e',
        remappings=[('/cmd_vel', '/teleop_cmd_vel')],
        output='screen',
    )


    return LaunchDescription([
        gz_sim,
        bridge,
        robot_state_publisher,
        pid_controller,
        rviz_node,
        rqt_reconfigure_node,
        teleop_node,
    ])
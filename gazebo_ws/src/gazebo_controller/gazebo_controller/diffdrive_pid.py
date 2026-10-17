import os
import xml.etree.ElementTree as ET
import numpy as np
import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory
from rcl_interfaces.msg import ParameterDescriptor, FloatingPointRange
from geometry_msgs.msg import Twist, PoseStamped
from tf2_ros import Buffer, TransformListener, TransformException




class DiffDrivePID(Node):
    def __init__(self):
        super().__init__('diffdrive_pid')


        # Read chassis length from worlds/maze_robot.sdf (fallback to 2.0m -> l = 1.0m)
        self.l = 1.0
        try:
            pkg_share = get_package_share_directory('gazebo_controller')
            sdf_path = os.path.join(pkg_share, 'worlds', 'maze_robot.sdf')
            root = ET.parse(sdf_path).getroot()
            size_elem = root.find(".//model[@name='vehicle_blue']/link[@name='chassis']/visual/geometry/box/size")
            if size_elem is not None and size_elem.text:
                chassis_length = float(size_elem.text.strip().split()[0])
                self.l = chassis_length / 2.0
        except Exception as e:
            self.get_logger().warn(f'Using default offset l=1.0m (could not parse SDF: {e})')


        # Declare tunable PD parameters with GUI slider ranges
        self.declare_parameter(
            'kp', 1.2,
            ParameterDescriptor(
                description='Proportional gain',
                floating_point_range=[FloatingPointRange(from_value=0.0, to_value=5.0, step=0.05)]
            )
        )
        self.declare_parameter(
            'kd', 0.15,
            ParameterDescriptor(
                description='Derivative gain',
                floating_point_range=[FloatingPointRange(from_value=0.0, to_value=2.0, step=0.01)]
            )
        )
        self.declare_parameter(
            'max_v', 1.5,
            ParameterDescriptor(
                description='Max linear velocity (m/s)',
                floating_point_range=[FloatingPointRange(from_value=0.1, to_value=5.0, step=0.1)]
            )
        )
        self.declare_parameter(
            'max_omega', 1.5,
            ParameterDescriptor(
                description='Max angular velocity (rad/s)',
                floating_point_range=[FloatingPointRange(from_value=0.1, to_value=5.0, step=0.1)]
            )
        )


        # Target goal [x_g, y_g]
        self.goal = None


        # Virtual point state for smoothed finite-difference velocity
        self.prev_vp_pos = None
        self.vp_vel = np.array([0.0, 0.0], dtype=float)


        # TF2 buffer & listener
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)


        # Subscribe to /goal_pose (from RViz2 2D Goal Pose tool)
        self.goal_sub = self.create_subscription(
            PoseStamped,
            '/goal_pose',
            self.goal_pose_callback,
            15
        )


        # Subscribe to /teleop_cmd_vel so any keypress cancels active goal and drives immediately
        self.teleop_sub = self.create_subscription(
            Twist,
            '/teleop_cmd_vel',
            self.teleop_callback,
            15
        )


        # Publish velocity commands to /cmd_vel (bridged to Gazebo)
        self.cmd_vel_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            15
        )


        # 30 Hz control loop
        self.dt = 1.0 / 30.0
        self.timer = self.create_timer(self.dt, self.timer_callback)


        self.get_logger().info(
            f'Gazebo DiffDrivePID started at 30 Hz (trailer-hitch offset l={self.l}m).'
        )


    def goal_pose_callback(self, msg: PoseStamped):
        x_g = msg.pose.position.x
        y_g = msg.pose.position.y
        self.goal = np.array([x_g, y_g], dtype=float)
        self.get_logger().info(f'New goal received: ({x_g:.3f}, {y_g:.3f})')


    def teleop_callback(self, msg: Twist):
        if self.goal is not None:
            self.goal = None
            self.get_logger().info('Teleop key pressed -> canceled active 2D Goal Pose.')
        self.cmd_vel_pub.publish(msg)


    def timer_callback(self):
        # 1. Lookup current robot pose from /tf
        try:
            trans = self.tf_buffer.lookup_transform(
                'car_world',
                'vehicle_blue/chassis',
                rclpy.time.Time()
            )
        except TransformException:
            try:
                trans = self.tf_buffer.lookup_transform(
                    'odom',
                    'chassis',
                    rclpy.time.Time()
                )
            except TransformException:
                return


        x_r = trans.transform.translation.x
        y_r = trans.transform.translation.y


        # Extract yaw angle theta_r from quaternion
        q = trans.transform.rotation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        theta_r = np.arctan2(siny_cosp, cosy_cosp)


        # 2. Compute virtual point (trailer hitch) position at front of robot
        x_p = x_r + self.l * np.cos(theta_r)
        y_p = y_r + self.l * np.sin(theta_r)
        vp_pos = np.array([x_p, y_p], dtype=float)


        # 3. Update virtual point velocity with Exponential Moving Average filter
        if self.prev_vp_pos is None:
            self.vp_vel = np.array([0.0, 0.0], dtype=float)
        else:
            raw_vel = (vp_pos - self.prev_vp_pos) / self.dt
            alpha = 0.2
            self.vp_vel = alpha * raw_vel + (1.0 - alpha) * self.vp_vel
        self.prev_vp_pos = vp_pos


        # If no goal is active, do not publish anything so teleop has full control
        if self.goal is None:
            return


        # 4. Compute position error of the virtual point
        error = self.goal - vp_pos
        dist_error = float(np.linalg.norm(error))


        cmd_msg = Twist()


        # Stop cleanly once the virtual point is within 20 cm of the goal, then clear goal
        if dist_error < 0.20:
            cmd_msg.linear.x = 0.0
            cmd_msg.angular.z = 0.0
            self.cmd_vel_pub.publish(cmd_msg)
            self.goal = None
            self.get_logger().info('Goal reached! Released /cmd_vel.')
            return


        # 5. Read live PD gains and compute world-frame control [ux, uy]
        kp = float(self.get_parameter('kp').value)
        kd = float(self.get_parameter('kd').value)
        max_v = float(self.get_parameter('max_v').value)
        max_omega = float(self.get_parameter('max_omega').value)


        ux = kp * error[0] - kd * self.vp_vel[0]
        uy = kp * error[1] - kd * self.vp_vel[1]


        # 6. Map [ux, uy] to differential drive commands [v_f, omega]
        v_f = np.cos(theta_r) * ux + np.sin(theta_r) * uy
        omega = (-np.sin(theta_r) * ux + np.cos(theta_r) * uy) / self.l


        # Clamp to realistic velocity limits
        v_f = np.clip(v_f, -max_v, max_v)
        omega = np.clip(omega, -max_omega, max_omega)


        cmd_msg.linear.x = float(v_f)
        cmd_msg.angular.z = float(omega)
        self.cmd_vel_pub.publish(cmd_msg)




def main(args=None):
    rclpy.init(args=args)
    node = DiffDrivePID()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()




if __name__ == '__main__':
    main()
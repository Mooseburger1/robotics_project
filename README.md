# Commands to run

## Launching the controller

```bash
source install/setup.bash
ros2 launch gazebo_controller gazebo_controller.launch.py
```

This will launch gazebo with the drone in the simulation environment. You can then launch teleop
twist to control the drone in the environment

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

You can also control the robot in `rviz2` by setting "goal poses" in the UI. You'll need to change

* Global Options -> Fixed Frame -> Chasis
* In the bottom left, click `add` -> Robot Model -> OK
* Then change RobotModel -> Description Topic -> /robot_description

This will add the robot to rviz and allow you to click `2d Goal Pose` and move the robot in rviz2
which in turn moves the robot in Gazebo Sim

For the PID controller that controlls the drone's speed, I have the module setup set that the kp
and kd values can be dynamically updated while the simulation is running using a widget with
sliders.

Just run

```bash
ros2 run rqt_reconfigure rqt_reconfigure
```

this will open up a qt widget. On the bottom left side of the widget, hit `Refresh`. Then select
`diffdrive_pid` from the menu on the left. This will open the slider widget so you can control
the PID constants dynamically while the simulator is running


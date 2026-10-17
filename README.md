# gazebo_controller — Differential Drive Robot in Gazebo Harmonic & ROS 2 Jazzy


This workspace (gazebo_ws) contains the gazebo_controller ROS 2 package for simulating and controlling a differential drive robot inside a Gazebo Harmonic maze world using both keyboard teleoperation (teleop_twist_keyboard) and a Trailer-Hitch PD controller (diffdrive_pid) driven by RViz2's **2D Goal Pose** tool.


---


## 1. Repository & Directory Structure
```text
robotics_project/
└── gazebo_ws/
    ├── Dockerfile
    ├── docker-compose.yml
    └── src/
        └── gazebo_controller/
            ├── package.xml
            ├── setup.cfg
            ├── setup.py
            ├── launch/
            │   └── gazebo_controller.launch.py
            ├── worlds/
            │   └── maze_robot.sdf
            ├── rviz/
            │   └── rviz.rviz
            └── gazebo_controller/
                ├── __init__.py
                └── diffdrive_pid.py
```

---


## 2. Prerequisites


* **[Git](https://git-scm.com/downloads)**
* **[Docker Desktop](https://docs.docker.com/get-docker/)** (or Docker Engine + Docker Compose v2 on Linux) with at least **8 GB RAM** allocated.
* **Display Setup for GUI Windows (Gazebo, RViz2, rqt_reconfigure, xterm):**
    * **Linux:** Run xhost +local: on your host machine before starting the container.
    * **Windows:** Start **XLaunch (VcXsrv)** with **Multiple windows**, Display number **0**, and **"Disable access control"** checked (or use the browser VNC desktop at http://127.0.0.1:6080/).
    * **macOS:** Open http://127.0.0.1:6080/ in your browser after starting the container to view the Ubuntu VNC desktop.

---


## 3. Setup & Build Instructions


### Step 1: Clone the Repository and Navigate to gazebo_ws
```bash
git clone <clone the repo>
cd robotics_project/gazebo_ws
```

### Step 2: Build and Start the Docker Container
```bash
docker compose up -d --build
```

### Step 3: Enter the Container and Build the ROS 2 Workspace
```bash
docker compose exec gazebo_controller bash
```

Inside the container (/ros2_ws), build and source the package:
```bash
cd /ros2_ws
colcon build --symlink-install
source ~/.bashrc
```

---


## 4. Running the Simulation


Inside the container terminal (/ros2_ws), run the launch file:
```bash
ros2 launch gazebo_controller gazebo_controller.launch.py
```

This single command automatically starts:
1. **Gazebo Harmonic (gz sim)** with the differential drive robot (vehicle_blue) inside the maze world (maze_robot.sdf).
2. **ROS-Gazebo Bridge (parameter_bridge)** bridging /cmd_vel, /tf, /odom, /joint_states, and /clock.
3. **Robot State Publisher (robot_state_publisher)** publishing the 3D robot description and link transforms.
4. **PD Controller (diffdrive_pid)** tracking goals published on /goal_pose.
5. **RViz2 (rviz2)** pre-configured with rviz/rviz.rviz.
6. **Dynamic Parameter Tuning GUI (rqt_reconfigure)** with live sliders for kp, kd, max_v, and max_omega.
7. **Keyboard Teleop (teleop_twist_keyboard)** in a dedicated xterm window.


---


## 5. Controlling the Robot


**Autonomous PD Goal Tracking (RViz2):**
* Click the **2D Goal Pose** button in the top toolbar of **RViz2**, then click and drag on the grid to set a target point. The robot will automatically drive to the goal and stop.

**Manual Keyboard Teleop (xterm Window):**
* Click inside the **teleop_twist_keyboard** xterm window and use i (forward), j (left), l (right), , (backward), and k (stop) to drive manually. Pressing any teleop key automatically cancels any active 2D Goal Pose.

**Live PD Gain Tuning (rqt_reconfigure):**
* In the **rqt_reconfigure** window, select **diffdrive_pid** in the left panel (click Refresh if needed) to adjust kp, kd, max_v, and max_omega in real time.
---


## 6. Useful Docker Commands (Run from robotics_project/gazebo_ws)


| Task | Command |
| :--- | :--- |
| Start container | docker compose up -d |
| Open a terminal inside the container | docker compose exec gazebo_controller bash |
| Stop container | docker compose down |
| Rebuild image (if Dockerfile changed) | docker compose up -d --build |
FROM tiryoh/ros2-desktop-vnc:jazzy


ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=jazzy
ENV GZ_VERSION=harmonic
ENV LIBGL_ALWAYS_SOFTWARE=1


# 1. Install Gazebo Harmonic, xterm, and ROS 2 packages inside the container
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    dos2unix \
    x11-apps \
    xterm \
    && curl https://packages.osrfoundation.org/gazebo.gpg \
       --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
       > /etc/apt/sources.list.d/gazebo-stable.list \
    && apt-get update && apt-get install -y \
    gz-harmonic \
    ros-jazzy-ros-gz-* \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-urdfdom-py \
    ros-jazzy-rqt-reconfigure \
    ros-jazzy-teleop-twist-keyboard \
    python3-colcon-common-extensions \
    python3-numpy \
    python3-scipy \
    python3-matplotlib \
    && rm -rf /var/lib/apt/lists/*


# 2. Auto-source ROS 2 Jazzy and the workspace in every terminal
RUN for rc in /etc/bash.bashrc /home/ubuntu/.bashrc /root/.bashrc; do \
        echo "umask 000" >> $rc && \
        echo "export GZ_VERSION=harmonic" >> $rc && \
        echo "export LIBGL_ALWAYS_SOFTWARE=1" >> $rc && \
        echo "source /opt/ros/jazzy/setup.bash" >> $rc && \
        echo "if [ -f /ros2_ws/install/setup.bash ]; then source /ros2_ws/install/setup.bash; fi" >> $rc; \
    done


WORKDIR /ros2_ws
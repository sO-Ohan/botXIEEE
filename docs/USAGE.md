# Usage guide

## Prerequisites

- Ubuntu host: 24.04 / 24.10 / 25.x / 26.x (x86_64 or arm64)
- `sudo` privileges (to install Podman/Distrobox on the host)
- A working internet connection
- ~5 GB free disk for the container + ROS 2 desktop

## 1. Get the scripts

```bash
git clone https://github.com/sO-Ohan/ros2-humble-distrobox.git
cd ros2-humble-distrobox
chmod +x setup-ros2-distrobox.sh install-ros2-humble.sh
```

## 2. Run the setup

```bash
./setup-ros2-distrobox.sh
```

This is idempotent — re-running it reuses an existing container instead of
recreating it. Expect it to take several minutes (mostly the ROS 2 apt
download).

### Configuration via environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `CONTAINER_NAME` | `ros2-humble` | Name of the Distrobox container |
| `UBUNTU_IMAGE` | `quay.io/toolbx-images/ubuntu-toolbox:22.04` | Base container image |
| `ROS_PACKAGE` | `ros-humble-desktop` | Set to `ros-humble-ros-base` for a minimal, headless install |

Examples:

```bash
# Minimal headless install
ROS_PACKAGE=ros-humble-ros-base ./setup-ros2-distrobox.sh

# Custom container name
CONTAINER_NAME=robot-dev ./setup-ros2-distrobox.sh

# Both
CONTAINER_NAME=robot-dev ROS_PACKAGE=ros-humble-ros-base ./setup-ros2-distrobox.sh
```

### `ros-humble-desktop` vs `ros-humble-ros-base`

| | `ros-humble-desktop` | `ros-humble-ros-base` |
| --- | --- | --- |
| Size | Larger (~3–4 GB) | Smaller (~1 GB) |
| GUI tools (RViz, rqt) | ✅ | ❌ |
| Demo nodes | ✅ | ❌ |
| Best for | Learning, visualization, workstations | Robots, CI, headless servers |

## 3. Enter the container

```bash
distrobox enter ros2-humble
```

ROS 2 is sourced automatically (the installer appended `source
/opt/ros/humble/setup.bash` to your `~/.bashrc`). Confirm:

```bash
ros2 --version
echo $ROS_DISTRO   # -> humble
```

## 4. Verify with talker/listener

**Terminal 1:**

```bash
distrobox enter ros2-humble
ros2 run demo_nodes_cpp talker
```

**Terminal 2:**

```bash
distrobox enter ros2-humble
ros2 run demo_nodes_cpp listener
```

The talker prints `Publishing: 'Hello World: N'` and the listener prints
`I heard: [Hello World: N]`. (Requires `ros-humble-desktop`.)

## 5. Create a workspace

Inside the container:

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
colcon build
source install/setup.bash
```

Because your `$HOME` is shared with the host, `~/ros2_ws` is visible from both
the host and the container.

## Lifecycle commands

| Action | Command |
| --- | --- |
| Enter | `distrobox enter ros2-humble` |
| Stop | `distrobox stop ros2-humble` |
| List | `distrobox list` |
| Remove | `distrobox rm ros2-humble` |
| Rebuild from scratch | `distrobox rm ros2-humble && ./setup-ros2-distrobox.sh` |

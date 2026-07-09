# ROS 2 Humble on Ubuntu 24/26 via Distrobox

Run **ROS 2 Humble Hawksbill** (the LTS that targets Ubuntu 22.04) on a newer
Ubuntu host (24.04 / 24.10 / 25.x / 26.x) without touching your host system.

The scripts use [Distrobox](https://distrobox.it/) to spin up an isolated
Ubuntu 22.04 container and install ROS 2 inside it.

## Why Humble?

ROS 2 **Humble Hawksbill** is the release officially built for Ubuntu 22.04
(Jammy) and is supported until **May 2027**. Newer Ubuntu releases don't have
first-class prebuilt ROS 2 binaries, so running Humble inside a 22.04 container
is the clean, supported path.

## What the scripts do

| Script | Runs on | Purpose |
| --- | --- | --- |
| `setup-ros2-distrobox.sh` | Host (Ubuntu 24/26) | Checks compatibility, installs Podman + Distrobox, creates the Ubuntu 22.04 container, then runs the inner installer |
| `install-ros2-humble.sh` | Inside the container | Installs ROS 2 Humble, dev tools, rosdep, and auto-sources it |

## Usage

```bash
chmod +x setup-ros2-distrobox.sh install-ros2-humble.sh
./setup-ros2-distrobox.sh
```

Then:

```bash
distrobox enter ros2-humble
ros2 run demo_nodes_cpp talker
```

### Options (environment variables)

| Variable | Default | Description |
| --- | --- | --- |
| `CONTAINER_NAME` | `ros2-humble` | Name of the Distrobox container |
| `UBUNTU_IMAGE` | `quay.io/toolbx-images/ubuntu-toolbox:22.04` | Base image |
| `ROS_PACKAGE` | `ros-humble-desktop` | Use `ros-humble-ros-base` for a minimal, headless install |

Example — minimal install in a custom container:

```bash
CONTAINER_NAME=my-ros ROS_PACKAGE=ros-humble-ros-base ./setup-ros2-distrobox.sh
```

## Verify

Terminal 1:

```bash
distrobox enter ros2-humble
ros2 run demo_nodes_cpp talker
```

Terminal 2:

```bash
distrobox enter ros2-humble
ros2 run demo_nodes_cpp listener
```

You should see the talker publishing and the listener receiving messages.

## Cleanup

```bash
distrobox stop ros2-humble
distrobox rm ros2-humble
```

## Requirements

- Ubuntu 24.04 / 24.10 / 25.x / 26.x host (x86_64 or arm64)
- `sudo` access to install host packages
- Internet connection

## Documentation

Detailed docs live in [`docs/`](docs/):

- [Overview](docs/OVERVIEW.md) — how it works and why Humble + Distrobox
- [Usage guide](docs/USAGE.md) — install, options, verification, lifecycle
- [Troubleshooting](docs/TROUBLESHOOTING.md) — fixes for common issues

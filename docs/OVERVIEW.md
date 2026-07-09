# Overview

This project lets you run **ROS 2 Humble Hawksbill** on a modern Ubuntu host
(24.04 / 24.10 / 25.x / 26.x) by installing it inside an isolated **Ubuntu
22.04 LTS** container managed by [Distrobox](https://distrobox.it/).

## The problem it solves

ROS 2 releases are tied to specific Ubuntu versions:

| ROS 2 release | Target Ubuntu | Support until |
| --- | --- | --- |
| **Humble Hawksbill** | 22.04 (Jammy) | May 2027 |
| Iron Irwini | 22.04 (Jammy) | Nov 2024 (EOL) |
| Jazzy Jalisco | 24.04 (Noble) | May 2029 |

If your host is Ubuntu 24.04 or newer, there are **no first-class prebuilt
Humble binaries** for it. Rather than compiling from source or downgrading your
whole machine, this project runs a lightweight Ubuntu 22.04 container where the
official Humble apt packages install cleanly — while still sharing your home
directory, GPU, USB devices, and network with the host (a Distrobox feature).

## Why Distrobox instead of plain Docker?

Distrobox is built on top of Podman/Docker but is tuned for **interactive
development**:

- Your `$HOME` is mounted automatically — your files, editors, and git config
  just work.
- Hardware access (USB serial, cameras, GPU) is passed through, which matters
  for robotics.
- `distrobox enter` drops you into a normal shell; no `docker exec` ceremony.
- Rootless by default with Podman.

## High-level flow

```
┌─────────────────────────── Host: Ubuntu 24 / 26 ───────────────────────────┐
│                                                                             │
│  setup-ros2-distrobox.sh                                                    │
│     1. check_compatibility   → verify OS, version, arch, namespaces         │
│     2. install_host_deps     → curl, Podman, Distrobox                      │
│     3. create_container      → Ubuntu 22.04 Distrobox container             │
│     4. install_ros           → run inner script inside the container ──┐    │
│                                                                        │    │
│   ┌──────────────── Container: Ubuntu 22.04 LTS ───────────────────┐   │    │
│   │  install-ros2-humble.sh                              <─────────┘   │    │
│   │     1. locale (UTF-8)                                              │    │
│   │     2. enable universe repo                                        │    │
│   │     3. add ROS 2 apt repository                                    │    │
│   │     4. apt install ros-humble-desktop + dev tools                  │    │
│   │     5. rosdep init/update                                          │    │
│   │     6. auto-source in ~/.bashrc                                     │    │
│   │     7. sanity check (ros2 --version)                               │    │
│   └────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

See [USAGE.md](USAGE.md) for how to run it and [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
if something goes wrong.

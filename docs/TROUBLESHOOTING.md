# Troubleshooting

## Compatibility check fails

**`This script only runs on Linux.`**
The host is not Linux. These scripts require an Ubuntu (or Ubuntu-like) host.

**`Architecture … has no prebuilt ROS 2 Humble packages.`**
ROS 2 Humble ships binaries only for `x86_64`/`amd64` and `aarch64`/`arm64`.
Other architectures (e.g. armhf, riscv64) would require building from source,
which these scripts don't do.

**`Unprivileged user namespaces appear disabled; rootless Podman may fail.`**
Rootless Podman needs user namespaces. Enable them:

```bash
sudo sysctl -w kernel.unprivileged_userns_clone=1
echo 'kernel.unprivileged_userns_clone=1' | sudo tee /etc/sysctl.d/00-userns.conf
```

## Podman / Distrobox installation issues

**`newuidmap`/`newgidmap` errors when creating the container.**
Install `uidmap` and make sure subuid/subgid ranges exist:

```bash
sudo apt-get install -y uidmap
grep "$USER" /etc/subuid /etc/subgid || \
  sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 "$USER"
```

Then log out and back in (or reboot) so the ranges take effect.

**Distrobox not found after install via the fallback method.**
The upstream installer places it in `~/.local/bin`. Ensure that's on your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Add that line to your `~/.bashrc` to make it permanent.

## Container creation is slow or hangs

The first `distrobox create` pulls the Ubuntu 22.04 image (~70 MB) and then
initializes it on first `enter`, which installs a handful of integration
packages. This is normal and only happens once. If it truly hangs, check your
network and DNS, then retry:

```bash
distrobox rm ros2-humble
./setup-ros2-distrobox.sh
```

## ROS 2 apt repository / GPG errors

**`The following signatures couldn't be verified …`**
The apt key didn't install. Re-run the inner installer inside the container:

```bash
distrobox enter ros2-humble -- bash -s < install-ros2-humble.sh
```

The script has a fallback that fetches the ROS key directly from
`raw.githubusercontent.com/ros/rosdistro/master/ros.key` if the
`ros2-apt-source` package can't be resolved.

**`Unable to locate package ros-humble-desktop`**
The ROS 2 repo wasn't added or `apt-get update` didn't run against it. Verify:

```bash
distrobox enter ros2-humble
cat /etc/apt/sources.list.d/ros2*.list   # should reference packages.ros.org
sudo apt-get update
```

## `ros2: command not found` inside the container

ROS 2 is installed but not sourced in your current shell. Either open a new
shell (the installer added sourcing to `~/.bashrc`) or run:

```bash
source /opt/ros/humble/setup.bash
```

## GUI tools (RViz, rqt) won't open

You installed `ros-humble-ros-base`, which has no GUI tools. Reinstall with the
desktop variant:

```bash
distrobox enter ros2-humble
sudo apt-get install -y ros-humble-desktop
```

If GUI apps still fail to display, Distrobox normally forwards X11/Wayland
automatically; make sure you launched from a graphical session and that
`echo $DISPLAY` (or `$WAYLAND_DISPLAY`) is non-empty inside the container.

## Nodes on host and container can't see each other

By default Distrobox shares the host network, so ROS 2 discovery works across
both. If you isolated the network or run multiple machines, set a matching
`ROS_DOMAIN_ID` in every shell:

```bash
export ROS_DOMAIN_ID=42
```

## Start over cleanly

```bash
distrobox stop ros2-humble
distrobox rm ros2-humble
./setup-ros2-distrobox.sh
```

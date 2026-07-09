#!/usr/bin/env bash
#
# install-ros2-humble.sh
#
# Runs INSIDE the Ubuntu 22.04 Distrobox container.
# Installs ROS 2 Humble Hawksbill — the LTS release paired with Ubuntu 22.04
# (Jammy), supported until May 2027.
#
# Configurable via env var:
#   ROS_PACKAGE=ros-humble-desktop     (default; includes demos, rviz, tools)
#   ROS_PACKAGE=ros-humble-ros-base    (minimal, no GUI)
#
set -Eeuo pipefail

ROS_DISTRO="humble"
ROS_PACKAGE="${ROS_PACKAGE:-ros-humble-desktop}"

log() { echo -e "\033[1;36m[ros2-install]\033[0m $*"; }

# Guard: this must run on Ubuntu 22.04 (Jammy).
# shellcheck disable=SC1091
. /etc/os-release
if [[ "${VERSION_ID:-}" != "22.04" ]]; then
  echo "ERROR: expected Ubuntu 22.04 inside the container, found ${VERSION_ID:-unknown}." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

# ---------------------------------------------------------------------------
# 1. Locale — ROS 2 requires a UTF-8 locale.
# ---------------------------------------------------------------------------
log "Configuring UTF-8 locale..."
sudo apt-get update -y
sudo apt-get install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# ---------------------------------------------------------------------------
# 2. Enable the Universe repo and base tooling.
# ---------------------------------------------------------------------------
log "Enabling Universe repository and installing prerequisites..."
sudo apt-get install -y software-properties-common curl
sudo add-apt-repository -y universe

# ---------------------------------------------------------------------------
# 3. Add the ROS 2 apt repository (modern ros2-apt-source package).
# ---------------------------------------------------------------------------
log "Adding the ROS 2 apt repository..."
ROS_APT_SOURCE_VERSION="$(curl -fsSL https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
  | grep -F '"tag_name"' | awk -F'"' '{print $4}')"

if [[ -n "${ROS_APT_SOURCE_VERSION}" ]]; then
  DEB="/tmp/ros2-apt-source.deb"
  curl -fsSL -o "${DEB}" \
    "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.${VERSION_CODENAME}_all.deb"
  sudo apt-get install -y "${DEB}"
  rm -f "${DEB}"
else
  # Fallback: classic keyring + source list method.
  log "Release lookup failed; using fallback keyring method..."
  sudo curl -fsSL -o /usr/share/keyrings/ros-archive-keyring.gpg \
    https://raw.githubusercontent.com/ros/rosdistro/master/ros.key
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu ${VERSION_CODENAME} main" \
    | sudo tee /etc/apt/sources.list.d/ros2.list >/dev/null
fi

# ---------------------------------------------------------------------------
# 4. Install ROS 2 Humble.
# ---------------------------------------------------------------------------
log "Installing ${ROS_PACKAGE} (this can take a while)..."
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y "${ROS_PACKAGE}"

# Development tools (colcon, rosdep, etc.) — handy and lightweight.
log "Installing ROS 2 development tools..."
sudo apt-get install -y ros-dev-tools python3-colcon-common-extensions

# ---------------------------------------------------------------------------
# 5. Initialize rosdep.
# ---------------------------------------------------------------------------
log "Initializing rosdep..."
sudo rosdep init 2>/dev/null || true
rosdep update || true

# ---------------------------------------------------------------------------
# 6. Auto-source ROS 2 in interactive shells.
# ---------------------------------------------------------------------------
SOURCE_LINE="source /opt/ros/${ROS_DISTRO}/setup.bash"
if ! grep -qxF "${SOURCE_LINE}" "${HOME}/.bashrc" 2>/dev/null; then
  log "Adding ROS 2 sourcing to ~/.bashrc..."
  {
    echo ""
    echo "# ROS 2 ${ROS_DISTRO}"
    echo "${SOURCE_LINE}"
  } >> "${HOME}/.bashrc"
fi

# ---------------------------------------------------------------------------
# 7. Sanity check.
# ---------------------------------------------------------------------------
log "Verifying installation..."
# shellcheck disable=SC1090
source "/opt/ros/${ROS_DISTRO}/setup.bash"
if command -v ros2 >/dev/null 2>&1; then
  log "SUCCESS: $(ros2 --version 2>/dev/null || echo "ros2 CLI available")"
  log "ROS_DISTRO=${ROS_DISTRO}  installed package=${ROS_PACKAGE}"
else
  echo "ERROR: 'ros2' command not found after installation." >&2
  exit 1
fi

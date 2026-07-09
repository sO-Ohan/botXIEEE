#!/usr/bin/env bash
#
# setup-ros2-distrobox.sh
#
# Host script for Ubuntu 24.04 / 24.10 / 25.x / 26.x.
#   1. Checks host compatibility.
#   2. Installs a container backend (Podman) + Distrobox if missing.
#   3. Creates an Ubuntu 22.04 LTS Distrobox container.
#   4. Installs ROS 2 Humble Hawksbill (the LTS for Ubuntu 22.04) inside it.
#
# ROS 2 Humble is the release matched to Ubuntu 22.04 (Jammy) and is
# supported until May 2027, which is why it is the right choice here.
#
# Usage:
#   ./setup-ros2-distrobox.sh                 # default container name "ros2-humble"
#   CONTAINER_NAME=my-ros ./setup-ros2-distrobox.sh
#
set -Eeuo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CONTAINER_NAME="${CONTAINER_NAME:-ros2-humble}"
UBUNTU_IMAGE="${UBUNTU_IMAGE:-quay.io/toolbx-images/ubuntu-toolbox:22.04}"
ROS_DISTRO="humble"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INNER_SCRIPT="${SCRIPT_DIR}/install-ros2-humble.sh"

# ---------------------------------------------------------------------------
# Pretty logging
# ---------------------------------------------------------------------------
if [[ -t 1 ]]; then
  C_INFO="\033[1;34m"; C_OK="\033[1;32m"; C_WARN="\033[1;33m"; C_ERR="\033[1;31m"; C_RST="\033[0m"
else
  C_INFO=""; C_OK=""; C_WARN=""; C_ERR=""; C_RST=""
fi
info()  { echo -e "${C_INFO}[*]${C_RST} $*"; }
ok()    { echo -e "${C_OK}[+]${C_RST} $*"; }
warn()  { echo -e "${C_WARN}[!]${C_RST} $*"; }
err()   { echo -e "${C_ERR}[x]${C_RST} $*" >&2; }
die()   { err "$*"; exit 1; }

trap 'err "Failed at line $LINENO. Aborting."' ERR

# ---------------------------------------------------------------------------
# 1. Compatibility checks
# ---------------------------------------------------------------------------
check_compatibility() {
  info "Checking host compatibility..."

  [[ "$(uname -s)" == "Linux" ]] || die "This script only runs on Linux."

  [[ -r /etc/os-release ]] || die "Cannot read /etc/os-release; unsupported host."
  # shellcheck disable=SC1091
  . /etc/os-release

  if [[ "${ID:-}" != "ubuntu" ]]; then
    warn "Host is '${ID:-unknown}', not Ubuntu. Distrobox may still work, continuing."
  fi

  local major="${VERSION_ID%%.*}"
  case "$major" in
    24|25|26)
      ok "Ubuntu ${VERSION_ID} detected — supported host."
      ;;
    *)
      warn "Ubuntu ${VERSION_ID:-unknown} is outside the tested 24/26 range."
      warn "Continuing anyway; Distrobox is version-agnostic."
      ;;
  esac

  # Architecture: ROS 2 Humble binaries ship for amd64 and arm64.
  local arch; arch="$(uname -m)"
  case "$arch" in
    x86_64|amd64|aarch64|arm64)
      ok "Architecture ${arch} is supported by ROS 2 Humble."
      ;;
    *)
      die "Architecture ${arch} has no prebuilt ROS 2 Humble packages."
      ;;
  esac

  # Kernel must support user namespaces for rootless Podman.
  if [[ -r /proc/sys/kernel/unprivileged_userns_clone ]]; then
    [[ "$(cat /proc/sys/kernel/unprivileged_userns_clone)" == "1" ]] \
      || warn "Unprivileged user namespaces appear disabled; rootless Podman may fail."
  fi

  command -v sudo >/dev/null 2>&1 || die "'sudo' is required to install host packages."

  ok "Compatibility check passed."
}

# ---------------------------------------------------------------------------
# 2. Install container backend + Distrobox on the host
# ---------------------------------------------------------------------------
install_host_deps() {
  info "Ensuring host dependencies (curl, podman, distrobox)..."

  local need_update=0
  for pkg in curl ca-certificates uidmap; do
    dpkg -s "$pkg" >/dev/null 2>&1 || need_update=1
  done

  if [[ "$need_update" == "1" ]]; then
    sudo apt-get update -y
    sudo apt-get install -y curl ca-certificates uidmap
  fi

  # Container backend: prefer an existing docker/podman, else install podman.
  if command -v podman >/dev/null 2>&1; then
    ok "Found podman: $(podman --version)"
  elif command -v docker >/dev/null 2>&1; then
    ok "Found docker: $(docker --version)"
  else
    info "Installing podman..."
    sudo apt-get update -y
    sudo apt-get install -y podman
    ok "podman installed: $(podman --version)"
  fi

  # Distrobox.
  if command -v distrobox >/dev/null 2>&1; then
    ok "Found distrobox: $(distrobox version 2>/dev/null || echo present)"
  else
    info "Installing distrobox..."
    if apt-cache show distrobox >/dev/null 2>&1; then
      sudo apt-get install -y distrobox
    else
      # Fall back to the upstream installer into ~/.local (no root needed).
      curl -fsSL https://raw.githubusercontent.com/89luca89/distrobox/main/install \
        | sh -s -- --prefix "$HOME/.local"
      export PATH="$HOME/.local/bin:$PATH"
    fi
    command -v distrobox >/dev/null 2>&1 || die "distrobox installation failed."
    ok "distrobox installed."
  fi
}

# ---------------------------------------------------------------------------
# 3. Create the Ubuntu 22.04 container
# ---------------------------------------------------------------------------
create_container() {
  info "Creating Ubuntu 22.04 Distrobox container '${CONTAINER_NAME}'..."

  if distrobox list 2>/dev/null | awk -F'|' '{gsub(/ /,"",$2); print $2}' | grep -qx "${CONTAINER_NAME}"; then
    warn "Container '${CONTAINER_NAME}' already exists — reusing it."
  else
    distrobox create \
      --name "${CONTAINER_NAME}" \
      --image "${UBUNTU_IMAGE}" \
      --yes
    ok "Container '${CONTAINER_NAME}' created."
  fi

  # Force first-time initialization so later commands run cleanly.
  distrobox enter "${CONTAINER_NAME}" -- true
}

# ---------------------------------------------------------------------------
# 4. Install ROS 2 Humble inside the container
# ---------------------------------------------------------------------------
install_ros() {
  info "Installing ROS 2 ${ROS_DISTRO} inside '${CONTAINER_NAME}'..."
  [[ -r "${INNER_SCRIPT}" ]] || die "Missing inner script: ${INNER_SCRIPT}"

  # Run the in-container installer non-interactively.
  distrobox enter "${CONTAINER_NAME}" -- bash -s < "${INNER_SCRIPT}"

  ok "ROS 2 ${ROS_DISTRO} installation finished."
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  check_compatibility
  install_host_deps
  create_container
  install_ros

  cat <<EOF

$(ok "All done!")

Your Ubuntu 22.04 + ROS 2 ${ROS_DISTRO} environment is ready.

Enter it with:

    distrobox enter ${CONTAINER_NAME}

Then, inside the container, ROS 2 is sourced automatically (added to ~/.bashrc).
Verify with:

    ros2 run demo_nodes_cpp talker
    # in another terminal (distrobox enter ${CONTAINER_NAME}):
    ros2 run demo_nodes_cpp listener

EOF
}

main "$@"

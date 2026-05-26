#!/bin/bash
#
# run.sh — Automation Script for USB File Transfer Activity Driver
#
# This Bash script automates the complete lifecycle of the USB audit
# driver project:
#   1. Builds the kernel module and user-space application.
#   2. Loads the kernel module with insmod.
#   3. Verifies the /dev/usb_audit device node exists.
#   4. Launches the user-space monitor application.
#   5. On exit, unloads the module and cleans up.
#
# Usage:
#   chmod +x scripts/run.sh
#   sudo ./scripts/run.sh [--interactive|--daemon]
#
# Project:  Group 10 — USB File Transfer Activity Driver (Project 15)
# Course:   CSC1107 — Operating Systems
# Target:   Raspberry Pi 4, Raspbian 64-bit

set -euo pipefail   # exit on error, undefined variable, or pipe failure

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------
MODULE_NAME="usb_audit"
DEVICE_NODE="/dev/${MODULE_NAME}"
MODULE_PATH="./src_kernel/${MODULE_NAME}.ko"
USER_APP="./src_user/usb_monitor"
RUN_MODE="${1:---interactive}"   # default: interactive menu

# Colour codes for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'   # No Colour

# -------------------------------------------------------------------------
# Helper: Print a coloured status banner
# -------------------------------------------------------------------------
banner() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
}

# -------------------------------------------------------------------------
# Helper: Print an info / error / success message
# -------------------------------------------------------------------------
info()    { echo -e "${CYAN}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[OK]${NC}    $1"; }
warning() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# -------------------------------------------------------------------------
# Cleanup handler — called on script exit (normal or interrupt)
# -------------------------------------------------------------------------
cleanup() {
    echo ""
    banner "Cleanup"

    # Kill the user-space app if it is still running.
    if [[ -n "${MONITOR_PID:-}" ]] && kill -0 "$MONITOR_PID" 2>/dev/null; then
        info "Stopping user-space monitor (PID $MONITOR_PID)..."
        kill "$MONITOR_PID" 2>/dev/null || true
        wait "$MONITOR_PID" 2>/dev/null || true
    fi

    # Unload the kernel module.
    if lsmod | grep -q "^${MODULE_NAME} "; then
        info "Unloading kernel module '${MODULE_NAME}'..."
        rmmod "${MODULE_NAME}" && success "Module unloaded." \
                                 || error "Failed to unload module."
    else
        info "Module '${MODULE_NAME}' is not loaded."
    fi

    echo ""
    success "Cleanup complete."
}

# Register the cleanup function for EXIT and common signals.
trap cleanup EXIT INT TERM

# -------------------------------------------------------------------------
# Step 1: Verify we are running as root
# -------------------------------------------------------------------------
banner "USB File Transfer Activity Driver — Group 10"

if [[ $EUID -ne 0 ]]; then
    error "This script must be run as root (use sudo)."
    exit 1
fi
success "Running with root privileges."

# -------------------------------------------------------------------------
# Step 2: Check that kernel headers are installed
# -------------------------------------------------------------------------
banner "Prerequisite Check"

if [[ ! -d "/lib/modules/$(uname -r)/build" ]]; then
    error "Kernel headers not found for $(uname -r)."
    info  "Install them with:"
    info  "  sudo apt update && sudo apt install raspberrypi-kernel-headers build-essential -y"
    exit 1
fi
success "Kernel headers found for $(uname -r)."

# -------------------------------------------------------------------------
# Step 3: Build the kernel module
# -------------------------------------------------------------------------
banner "Building Kernel Module"

info "Compiling ${MODULE_NAME}.ko..."
make -C src_kernel clean > /dev/null 2>&1 || true
if make -C src_kernel; then
    success "Kernel module built successfully."
else
    error "Kernel module compilation failed."
    exit 1
fi

# -------------------------------------------------------------------------
# Step 4: Build the user-space application
# -------------------------------------------------------------------------
banner "Building User-Space Application"

info "Compiling usb_monitor..."
if gcc -Wall -Wextra -O2 -I./include -o "${USER_APP}" src_user/usb_monitor.c; then
    success "User-space application built successfully."
else
    error "User-space compilation failed."
    exit 1
fi

# -------------------------------------------------------------------------
# Step 5: Load the kernel module
# -------------------------------------------------------------------------
banner "Loading Kernel Module"

# Remove the module first if it is already loaded (idempotent).
if lsmod | grep -q "^${MODULE_NAME} "; then
    info "Module already loaded.  Removing first..."
    rmmod "${MODULE_NAME}" || true
    sleep 1
fi

info "Inserting ${MODULE_NAME}.ko..."
if insmod "${MODULE_PATH}"; then
    success "Module loaded."
else
    error "insmod failed.  Check dmesg for details."
    exit 1
fi

# -------------------------------------------------------------------------
# Step 6: Verify the device node
# -------------------------------------------------------------------------
banner "Device Node Verification"

if [[ -e "${DEVICE_NODE}" ]]; then
    success "Device node ${DEVICE_NODE} exists."
    ls -la "${DEVICE_NODE}"
else
    error "Device node ${DEVICE_NODE} was not created."
    error "Check dmesg | tail -20 for kernel messages."
    exit 1
fi

# Set permissions so non-root can also read (optional, for testing).
chmod 666 "${DEVICE_NODE}" 2>/dev/null || true

# -------------------------------------------------------------------------
# Step 7: Show recent kernel logs
# -------------------------------------------------------------------------
banner "Recent Kernel Logs (dmesg)"

dmesg | tail -10

# -------------------------------------------------------------------------
# Step 8: Launch the user-space monitor
# -------------------------------------------------------------------------
banner "Launching User-Space Monitor"

if [[ -x "${USER_APP}" ]]; then
    info "Starting monitor in ${RUN_MODE} mode..."
    info "Press Ctrl+C to stop."

    # Run in foreground so the trap can catch Ctrl+C.
    "${USER_APP}" "${RUN_MODE}" &
    MONITOR_PID=$!

    wait "${MONITOR_PID}" || true
    success "Monitor exited."
else
    error "User-space application not found or not executable: ${USER_APP}"
    exit 1
fi

# Cleanup runs automatically via the trap.

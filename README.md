# Group 10 — Project 15: USB File Transfer Activity Driver

A **Linux kernel module driver** that monitors file transfer activity on removable USB storage devices, paired with **user-space tools** for real-time logging, statistics, and automatic anomaly detection. Designed for **data loss prevention (DLP)** and **cybersecurity auditing** on the **Raspberry Pi 4 (Raspbian 64-bit)**.

---

## Table of Contents

1. [Directory Structure](#directory-structure)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Manual Build & Run](#manual-build--run)
5. [Features](#features)
6. [User-Space Applications](#user-space-applications)
7. [Anomaly Detection](#anomaly-detection)
8. [Automated Testing](#automated-testing)
9. [Verification Checklist](#verification-checklist)
10. [Troubleshooting](#troubleshooting)
11. [Generating the Report](#generating-the-report)

---

## Directory Structure

```text
OS-Grp-10/
├── README.md
├── GUIDE.md                        # Beginner-friendly walkthrough
├── Makefile                        # Top-level build orchestration
├── .gitignore
│
├── include/
│   └── usb_tracker.h               # Shared header: ioctl commands, data structs
│
├── src_kernel/                     # Linux Kernel Module (LKM)
│   ├── Makefile                    # Kbuild for module compilation
│   └── usb_audit.c                 # Char device driver + kprobe + anomaly engine
│
├── src_user/                       # User-space applications
│   ├── usb_monitor.c               # C dashboard (interactive + daemon mode)
│   └── file_tracker.py             # Python watchdog (real-time file monitoring)
│
└── scripts/
    ├── run.sh                      # Full lifecycle automation
    ├── test_all.sh                 # Automated 22-test verification suite
    └── generate_report.py          # python-docx report generator
```

---

## Prerequisites

- **Raspberry Pi 4** running Raspbian 64-bit (or any Linux system with kernel headers)
- A USB storage device for real-hardware testing

### Install Dependencies

```bash
sudo apt update
sudo apt install raspberrypi-kernel-headers build-essential python3 -y
pip install watchdog python-docx
```

### Find Your USB Drive

```bash
lsblk                          # Note the MOUNTPOINT (e.g. /media/pi/SAMSUNG)
```

> Update `USB_TARGET_PATH` in `src_user/file_tracker.py` to match your mount point.

---

## Quick Start

### One Command (Automated)

```bash
chmod +x scripts/run.sh
sudo ./scripts/run.sh
```

This handles: check prerequisites → build → load module → verify → launch monitor → cleanup on exit.

### Run All 22 Automated Tests

```bash
chmod +x scripts/test_all.sh
sudo ./scripts/test_all.sh
```

Produces a colour-coded pass/fail report. All 22 tests should pass.

---

## Manual Build & Run

```bash
# Build everything
make all

# Load the kernel module
sudo insmod src_kernel/usb_audit.ko

# Verify it loaded
lsmod | grep usb_audit
ls -la /dev/usb_audit
dmesg | tail -10

# Launch the C monitor
sudo ./src_user/usb_monitor -p "/media/pi/YOUR_USB"

# Or launch the Python watchdog
python3 src_user/file_tracker.py

# When done, unload
sudo rmmod usb_audit
make clean
```

---

## Features

### Kernel Module (`usb_audit.ko`)

| Feature | Description |
|---|---|
| **Character device** | `/dev/usb_audit` — user-space talks to the driver through standard file ops |
| **USB hotplug detection** | Automatically logs DEVICE_IN / DEVICE_OUT on plug/unplug |
| **Circular log buffer** | 128-entry ring buffer; oldest entries overwritten when full |
| **File size tracking** | Parses `(N bytes)` suffix from user-space events; kprobe captures real byte counts |
| **kprobe interception** | Hooks `vfs_write()` — autonomously detects file writes without user-space help |
| **Dual-path logging** | Atomic-safe path (kprobe context) + regular path (user context), both using monotonic timestamps |
| **ioctl API** | 7 commands: GET_STATS, CLEAR_LOGS, SET_PATH, GET_LOGS, RESET_STATS, SET_ANOMALY, GET_ANOMALY |
| **Anomaly engine** | Sliding-window burst detector with configurable threshold and cooldown |
| **Kernel 6.4+ compat** | Preprocessor version check for `class_create()` API change |
| **Module parameter** | `enable_vfs_kprobe` (bool) — disable kprobe at load time if needed |

### User-Space C Application (`usb_monitor`)

| Feature | Description |
|---|---|
| **Interactive mode** | 11 commands: C/M/D events, A alert, T config, S stats, L logs, R/X reset/clear, Q quit |
| **Daemon mode** | Live dashboard refreshing every 2 seconds |
| **CLI flags** | `-p` path, `-t` threshold, `-w` window, `-d` daemon, `-i` interactive, `-h` help |
| **Auto anomaly check** | Queries kernel alert status after every file event |

### Python Watchdog (`file_tracker.py`)

| Feature | Description |
|---|---|
| **Real-time monitoring** | Watches folder for create/modify/close/delete events using watchdog library |
| **Kernel integration** | Sends events to `/dev/usb_audit` with real file sizes via `send_kernel_event()` |
| **Standalone mode** | Works even without the kernel module loaded |
| **Local anomaly detection** | Independent sliding-window detector |

---

## User-Space Applications

### C Monitor (`usb_monitor`)

```
Usage: ./usb_monitor [OPTIONS]

Options:
  -i, --interactive      Interactive test menu (default)
  -d, --daemon           Periodic dashboard refresh mode
  -p, --path <path>      USB mount path to monitor
  -t, --threshold <n>    Max file ops before alert (default: 5)
  -w, --window <ms>      Sliding window in ms (default: 3000)
  -h, --help             Show help
```

**Interactive commands:**

| Command | Description |
|---|---|
| `C <path>` | Report file CREATE |
| `M <path>` | Report file MODIFY |
| `D <path>` | Report file DELETE |
| `A` | Manually trigger ALERT |
| `T <n> <ms>` | Set anomaly threshold & window |
| `S` | Show statistics + anomaly status |
| `L` | Show recent log entries |
| `R` | Reset all counters + anomaly ring |
| `X` | Clear log buffer |
| `Q` | Quit |

### Python Watchdog (`file_tracker.py`)

```bash
python3 src_user/file_tracker.py
```

Monitors the configured USB path in real time. Sends create/modify/delete events to the kernel module with actual file sizes. Has independent anomaly detection with configurable threshold (5 ops) and window (3.0 seconds).

---

## Anomaly Detection

The mass-copy detection engine runs at **three independent layers**:

### 1. Kernel-Side Auto-Detection

- 64-entry ring buffer of event timestamps
- After each CREATE/MODIFY, counts events within the sliding window
- If count > threshold AND cooldown (5s) elapsed → auto-logs SECURITY ALERT
- Fed by **both** the kprobe path (automatic) and the user-space write() path (injected)
- Both paths use consistent monotonic timestamps (`ktime_get_ns`)
- Configurable via `USB_AUDIT_SET_ANOMALY` / `USB_AUDIT_GET_ANOMALY` ioctls

### 2. User-Space Polling

- C monitor calls `GET_ANOMALY` ioctl after each event
- Displays red **SECURITY ALERT** banner if `alert_triggered == 1`
- Daemon mode checks every refresh cycle

### 3. Python-Side Detection

- Independent sliding-window implementation in `file_tracker.py`
- Prints `[SECURITY ALERT]` on console

### Testing Mass-Copy Detection

```bash
# In the interactive monitor:
T 2 5000                     # Threshold=2 ops, window=5000ms
C /media/usb/a.txt           # Event 1
C /media/usb/b.txt           # Event 2
C /media/usb/c.txt           # Event 3 — ALERT!

# Verify in kernel logs:
dmesg | grep "SECURITY ALERT"
# → [usb_audit] *** SECURITY ALERT *** Mass-copy detected!  3 file ops within 5000 ms (threshold=2)
```

---

## Automated Testing

The project includes `scripts/test_all.sh` — a comprehensive automated test suite:

```bash
sudo ./scripts/test_all.sh
```

**22 tests across 10 categories:**

| Category | Tests |
|---|---|
| Module loading | Load success |
| Device node | `/dev/usb_audit` exists |
| Kernel log | Driver loaded, kprobe active, notifier registered |
| Monitor connection | Connected to device, path set correctly |
| Event injection | CREATE, MODIFY, DELETE accepted |
| Statistics | Create/Modify/Delete counters = 1 |
| Log buffer | FILE_CREATE, FILE_MODIFY, FILE_DELETE entries present |
| Anomaly detection | Alert triggered, kernel also logged |
| USB drive | Mount point exists, can write test file |
| Clean shutdown | Module unloads (or gracefully skipped if in use) |

**Verified on:** Raspberry Pi 4, kernel 6.18.26-v71-CSC1107_CUSTOM_KERNEL+, USB drive at `/media/colossalblue/RAZER`. **Result: 22/22 passed.**

---

## Verification Checklist

| # | Feature | How to Verify | Status |
|---|---|---|---|
| 1 | Module compiles | `make all` exits 0 | ✅ |
| 2 | Module loads | `insmod` succeeds; `/dev/usb_audit` created | ✅ |
| 3 | kprobe active | `dmesg` shows kretprobe registered | ✅ |
| 4 | Hotplug notifier | `dmesg` shows notifier registered | ✅ |
| 5 | Monitor connects | `usb_monitor` shows "Connected" | ✅ |
| 6 | Event injection | C/M/D commands produce "Sent event" | ✅ |
| 7 | Stats accurate | S command shows correct counters | ✅ |
| 8 | Log buffer works | L command shows timestamped entries | ✅ |
| 9 | Anomaly alert | 3 rapid events trigger SECURITY ALERT | ✅ |
| 10 | Kernel alert logged | `dmesg` shows alert with burst details | ✅ |
| 11 | USB drive I/O | Write/read real files on USB | ✅ |
| 12 | Clean unload | `rmmod` succeeds | ✅ |
| 13 | All 22 auto-tests | `test_all.sh` reports 22/22 | ✅ |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `make` fails with missing headers | `sudo apt install raspberrypi-kernel-headers` |
| `insmod` fails: enable_kprobe redeclared | Fixed — renamed to `enable_vfs_kprobe` |
| `insmod` fails: implicit declaration | Fixed — added forward declaration for `anomaly_check_burst` |
| `insmod` fails: case label not constant | Fixed — ioctl `GET_LOGS` size overflow worked around |
| `insmod` fails: Operation not permitted | Run with `sudo` |
| `insmod` fails: Invalid module format | Kernel headers mismatch; reboot after kernel update |
| `/dev/usb_audit` not created | Check `dmesg` for errors |
| `usb_monitor` cannot open device | Module not loaded: `lsmod \| grep usb_audit` |
| USB notifier not firing | Check device class is mass-storage: `lsusb -v` |
| Python can't find mount point | Update `USB_TARGET_PATH` in `file_tracker.py` |
| Mount is read-only (NTFS) | Use `sudo` for file operations |
| Undervoltage detected | Use official Pi power supply or a USB flash drive instead of HDD |

---

## Generating the Report

```bash
# Requires python-docx (pip install python-docx)
python3 scripts/generate_report.py
```

Output: `scripts/Px_Group10-report-CSC1107.docx`

Uses `python-docx` library for clean, maintainable document generation — no hand-crafted XML.

---

*Group 10 — CSC1107 Operating Systems — Project 15*

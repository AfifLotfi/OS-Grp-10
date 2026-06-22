# The Absolute Beginner's Guide to Our USB File Transfer Activity Driver

---

> **Who is this for?** Anyone who looks at this project and thinks *"I have no idea what any of this means."*
>
> By the time you finish reading, you'll understand exactly what we built, why we built it, and how every piece fits together.

---

## Table of Contents

1. [What Problem Are We Solving?](#1-what-problem-are-we-solving)
2. [The Big Picture: How a Computer Runs Code](#2-the-big-picture-how-a-computer-runs-code)
3. [User-Space vs. Kernel-Space](#3-user-space-vs-kernel-space-the-two-worlds)
4. [What Is a "Driver"?](#4-what-is-a-driver-and-why-do-we-need-one)
5. [Our Project: The Bird's-Eye View](#5-our-project-the-birds-eye-view)
6. [The Layers of Our System](#6-the-layers-of-our-system)
7. [File-by-File Walkthrough](#7-file-by-file-walkthrough)
8. [How to Build and Run (Step by Step)](#8-how-to-build-and-run-it-step-by-step)
9. [Testing the Mass-Copy Alert](#9-how-to-test-the-mass-copy-alert)
10. [Automated Testing](#10-automated-testing)
11. [Glossary: Jargon Buster](#11-glossary-jargon-buster)

---

## 1. What Problem Are We Solving?

Imagine you work at a company that handles sensitive data. An employee plugs in a USB thumb drive and starts copying hundreds of confidential files. How would you know? How would you stop it?

Our project is a **surveillance system for USB drives**. It watches every file that gets written to a USB stick and, if someone copies too many files too quickly (suspicious "mass-copy" behaviour), it **automatically raises an alarm**.

This is called **Data Loss Prevention (DLP)** — stopping sensitive data from walking out the door on a tiny USB stick.

---

## 2. The Big Picture: How a Computer Runs Code

Think of a computer like a **restaurant**:

| Restaurant Analogy | Computer Equivalent |
|---|---|
| The **kitchen** — where food is prepared, stoves are controlled. Only the chef has access. | The **kernel** — the core of the OS. It controls CPU, memory, and all hardware. |
| The **dining room** — where customers sit and order. They only see what the waiter brings. | **User-space** — where your apps live (browser, text editor, games). |
| The **waiter** — takes orders to the kitchen and brings food back. | **System calls** — how apps ask the kernel to do things. |

**Key idea:** Apps can't touch hardware directly. They must *ask the kernel*. The kernel is the boss.

---

## 3. User-Space vs. Kernel-Space: The Two Worlds

```
┌─────────────────────────────────────────┐
│              USER-SPACE                  │
│  (Your apps: browser, VS Code, etc.)    │
│                                          │
│  ✅ Can: open files, print text, play   │
│         music, browse the web            │
│  ❌ Can't: talk to USB ports directly   │
├─────────────────────────────────────────┤
│             KERNEL-SPACE                 │
│  (The Linux kernel — the "brain")       │
│                                          │
│  ✅ Can: control ALL hardware           │
│  ✅ Has: absolute power                 │
└─────────────────────────────────────────┘
```

**Why separate them?** Safety. If a buggy app crashes, only that app dies. If the kernel crashed, the whole computer freezes.

---

## 4. What Is a "Driver" and Why Do We Need One?

A **driver** is kernel code that teaches the kernel how to talk to hardware.

| Without a driver | With a driver |
|---|---|
| You plug in a USB stick. The kernel sees "something" but doesn't know what to do with it. | The USB driver says "I know how to talk to this!" Now it works. |

**We wrote a custom driver.** Not to *use* the USB stick (Linux already does that), but to **watch and log** every file operation happening on it. Think of it as a security camera installed *inside* the kernel.

---

## 5. Our Project: The Bird's-Eye View

Here's what happens when our system is running:

```
1. You plug in a USB stick
       │
       ▼
2. Our kernel driver detects it → logs "DEVICE INSERTED"
       │
       ▼
3. You copy a file to the USB stick
       │
       ▼
4. TWO things happen simultaneously:
   a) The kernel's kprobe automatically detects the write → logs it
   b) The user-space monitor sees the change → sends an event to the driver
       │
       ▼
5. Both paths feed into the same anomaly detection engine
       │
       ▼
6. You copy many files rapidly (suspicious!)
       │
       ▼
7. The driver AUTOMATICALLY raises a SECURITY ALERT 🚨
       │
       ▼
8. The dashboard shows the alert; dmesg has a permanent record
```

All of this is **logged permanently** in the kernel's message buffer (`dmesg`) and can be retrieved at any time.

---

## 6. The Layers of Our System

### Layer 1: The Kernel Module (`usb_audit.ko`)
- Lives in **kernel-space**
- Creates a "virtual file" at `/dev/usb_audit` that user apps can talk to
- Watches for USB devices being plugged in / unplugged
- Has a **kprobe** that hooks into the kernel's own file-writing function — so it automatically detects every file write without any app needing to tell it
- Maintains a **circular buffer** (128 entries) of recent events
- Runs the **anomaly detection engine**

### Layer 2: The User-Space C Application (`usb_monitor`)
- A normal terminal program
- Opens `/dev/usb_audit` and talks to the kernel using **ioctl**
- Shows a dashboard with statistics, logs, and alerts
- Lets you inject test events to verify the system works
- Has interactive and daemon (auto-refresh) modes

### Layer 3: The Python Watchdog (`file_tracker.py`)
- An alternative monitor using the `watchdog` library
- Watches the USB folder in real time for file changes
- Sends events to the kernel module with real file sizes
- Has its own independent anomaly detector
- Works even without the kernel module loaded

### Layer 4: The Automation Scripts
- `run.sh` — one command does everything: build, load, run, cleanup
- `test_all.sh` — runs 22 automated tests; tells you if everything works
- `generate_report.py` — creates the Word document report

```
┌──────────────────────────────────────────────────────┐
│                    USER-SPACE                         │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │usb_monitor│  │file_tracker  │  │test_all.sh    │  │
│  │ (C app)  │  │   (.py)      │  │ (auto tests)  │  │
│  └────┬─────┘  └──────┬───────┘  └───────┬───────┘  │
│       │               │                   │          │
│       │    ioctl()    │   write()         │  runs    │
│       ▼               ▼                   ▼          │
├──────────────────────────────────────────────────────┤
│                  KERNEL-SPACE                         │
│  ┌──────────────────────────────────────────────┐    │
│  │           usb_audit.ko (our driver)          │    │
│  │  ┌────────┐ ┌──────────┐ ┌────────────────┐ │    │
│  │  │  USB   │ │ Circular │ │   Anomaly      │ │    │
│  │  │Notifier│ │ Log Buf  │ │   Detector     │ │    │
│  │  └────────┘ └──────────┘ └────────────────┘ │    │
│  │  ┌──────────────────────────────────────┐   │    │
│  │  │  kprobe on vfs_write (auto-detect)   │   │    │
│  │  └──────────────────────────────────────┘   │    │
│  └──────────────────────────────────────────────┘    │
│                      │                                │
│              /dev/usb_audit                           │
│           (character device)                          │
└──────────────────────────────────────────────────────┘
```

---

## 7. File-by-File Walkthrough

### `include/usb_tracker.h` — The "Contract"

The **header file** that defines data structures both the kernel module and user apps agree on.

| Concept | Plain English |
|---|---|
| `usb_audit_log_entry_t` | A single event: "At time X, PID Y created file Z (size: 1024 bytes)" |
| `usb_audit_stats_t` | Running totals: "42 files created, 3 MB written, 2 alerts" |
| `usb_audit_anomaly_t` | Anomaly config: "Alert if >5 file ops in 3000 ms" |
| `USB_AUDIT_GET_STATS` | ioctl command: "Kernel, give me the statistics" |
| `USB_AUDIT_SET_ANOMALY` | ioctl command: "Kernel, change the threshold to 10" |

> One tricky problem we solved: the `GET_LOGS` structure is 35 KB — too big for the kernel's ioctl size field (max 16 KB). We used a placeholder type in the macro definition to keep the command number valid.

### `src_kernel/usb_audit.c` — The Kernel Module (The Brain)

The most important file. Runs **inside the Linux kernel**.

#### Module Registration
```c
module_init(usb_audit_init);
module_exit(usb_audit_exit);
```
`insmod` calls `usb_audit_init()`. `rmmod` calls `usb_audit_exit()`. These are the "on" and "off" switches.

#### Character Device
Creates `/dev/usb_audit` — a "pipe" between user apps and the driver. Apps read to get logs, write to inject events, and use ioctl for commands.

#### USB Hotplug Notifier
Tells the kernel: "Tell me whenever a USB storage device is plugged in or removed." Our function checks the device class and logs DEVICE_IN or DEVICE_OUT events.

#### kprobe — Automatic File Write Detection
This is a key feature. A **kretprobe** hooks into `vfs_write()`, the kernel's own file-writing function. Every time any program writes a file anywhere on the system, our probe fires. It checks: "Is this file on the monitored USB path?" If yes, it logs the event automatically — no user app needed.

The challenge: kprobe handlers run in a special mode where they can't sleep. Regular locks (mutexes) can sleep, so they'd crash the kernel. We solved this with a special "trylock" that either grabs the lock instantly or skips the event. Safe.

#### Circular Log Buffer
A fixed-size array (128 slots) that wraps around. When full, oldest entries get overwritten. No infinite memory growth.

```
Position:  0    1    2   ...  125  126  127
         ┌────┬────┬────┬───┬─────┬─────┬─────┐
         │ ev1│ ev2│ ev3│...│     │     │     │
         └────┴────┴────┴───┴─────┴─────┴─────┘
           ↑                        ↑
         tail (oldest)           head (next write)
```

#### Anomaly Detection Engine (The Secret Sauce)
1. Every file CREATE or MODIFY records its **timestamp** in a 64-slot ring.
2. After recording, count: "How many timestamps are within the last 3 seconds?"
3. If count > 5 AND 5 seconds since last alert → **SECURITY ALERT!**
4. The cooldown prevents alert spam during sustained copying.

```
Timeline:
t=0.0  ──► CREATE file1.txt  (ring: [0.0])
t=0.4  ──► CREATE file2.txt  (ring: [0.0, 0.4])
t=0.8  ──► CREATE file3.txt  (ring: [0.0, 0.4, 0.8])
t=1.2  ──► CREATE file4.txt  (ring: [0.0, 0.4, 0.8, 1.2])
t=1.6  ──► CREATE file5.txt  (ring: [0.0, 0.4, 0.8, 1.2, 1.6])
t=2.0  ──► CREATE file6.txt  (ring: [0.0, 0.4, 0.8, 1.2, 1.6, 2.0])
                               ↑ 6 entries in 3s → ALERT! 🚨
```

Two important details: (1) the anomaly engine is fed by **both** the kprobe path (automatic) and user-space events (injected), (2) both paths use the same clock type (monotonic) so timestamps are consistent.

### `src_user/usb_monitor.c` — The Dashboard

A C program that talks to the driver via ioctl. Key features:
- **Interactive mode:** A menu where you type commands (`C /path` to simulate file creation, `S` for stats, `L` for logs)
- **Daemon mode:** Dashboard refreshing every 2 seconds
- **Auto-check:** After each event, asks the kernel "Did that trigger an alert?" and shows a warning banner if so
- **Configurable:** Set path, threshold, and window via command-line flags

### `src_user/file_tracker.py` — The Python Watchdog

Watches the USB folder in real time. Detects file creation, modification, closing, and deletion. Sends events to the kernel module through `/dev/usb_audit` with the real file size. Has its own sliding-window anomaly detector as a backup.

### `scripts/run.sh` — The One-Click Launcher

Does everything: checks root, verifies headers, builds, loads module, verifies device, launches monitor, cleans up on Ctrl+C.

### `scripts/test_all.sh` — The Automated Tester

Runs 22 tests covering every feature. Produces a pass/fail report. Verifies: module loading, device node, kprobe status, notifier, monitor connection, event injection (C/M/D), statistics accuracy, log buffer, anomaly detection, USB drive I/O, clean shutdown.

### `scripts/generate_report.py` — The Report Generator

Creates the Word document report using the `python-docx` library. No hand-crafted XML — just clean Python code.

---

## 8. How to Build and Run It (Step by Step)

> ⚠️ **You need a Raspberry Pi 4 running Raspbian 64-bit** (or any Linux with kernel headers).

### Step 1: Install tools
```bash
sudo apt update
sudo apt install raspberrypi-kernel-headers build-essential -y
```

### Step 2: Clone and build
```bash
git clone https://github.com/AfifLotfi/OS-Grp-10.git
cd OS-Grp-10
make all
```

This produces:
- `src_kernel/usb_audit.ko` — the kernel module
- `src_user/usb_monitor` — the user-space app

### Step 3: Load the driver
```bash
sudo insmod src_kernel/usb_audit.ko
ls -la /dev/usb_audit    # should show the device file
dmesg | tail -5          # should show "Driver loaded successfully"
```

### Step 4: Run the monitor
```bash
sudo ./src_user/usb_monitor --interactive
```

### Step 5: Test it
At the `Command →` prompt:
```
S               ← Show statistics (should be all zeros)
C test.txt      ← Simulate file CREATE
M test.txt      ← Simulate file MODIFY
D test.txt      ← Simulate file DELETE
S               ← Counters should be 1 each
L               ← Show log entries
Q               ← Quit
```

### Step 6: Test mass-copy alert
```
T 2 5000        ← Threshold=2, window=5000ms
C a.txt         ← Event 1
C b.txt         ← Event 2
C c.txt         ← Event 3 — ALERT! 🚨
```

### Step 7: Unload
```bash
sudo rmmod usb_audit
```

### Or just run the script!
```bash
sudo ./scripts/run.sh
```

---

## 9. How to Test the Mass-Copy Alert

### Via the C monitor
```
T 2 5000          ← Set threshold: 2 ops in 5000ms
C a.txt
C b.txt
C c.txt           ← ALERT! 🚨
```

### Verify in kernel logs
```bash
dmesg | grep "SECURITY ALERT"
# → [usb_audit] *** SECURITY ALERT *** Mass-copy detected!
#   3 file ops within 5000 ms (threshold=2)
```

### With custom thresholds
```bash
# Alert after 4 files within 2 seconds:
sudo ./src_user/usb_monitor -i -t 3 -w 2000
```

### Real file copy test
```bash
# Create 10 files rapidly on the USB drive:
for i in $(seq 1 10); do echo "data$i" > /media/pi/USB/mass_$i.txt; done
# The kprobe auto-detects these writes and the anomaly engine fires!
```

---

## 10. Automated Testing

Run the test suite to verify everything works:

```bash
sudo ./scripts/test_all.sh
```

It checks 22 things automatically:
- ✅ Module loads and creates `/dev/usb_audit`
- ✅ kprobe registered on vfs_write
- ✅ USB notifier registered
- ✅ Monitor connects and sets path
- ✅ Event injection works (C/M/D)
- ✅ Statistics counters are accurate
- ✅ Log buffer stores entries
- ✅ Anomaly detection triggers alerts
- ✅ Real USB drive is writable
- ✅ Clean shutdown works

**Result on our test Pi: 22/22 passed.**

---

## 11. Glossary: Jargon Buster

| Term | What It Actually Means |
|---|---|
| **Kernel** | The core of the OS. The boss of all hardware. |
| **User-space** | Where normal apps run. Limited access. |
| **Kernel module (.ko)** | A plugin for the kernel. Load/unload without rebooting. |
| **Driver** | Code that teaches the kernel to talk to hardware. |
| **Character device** | A virtual file like `/dev/usb_audit` — a pipe between an app and a driver. |
| **insmod** | "Insert Module" — loads a `.ko` file into the kernel. |
| **rmmod** | "Remove Module" — unloads a kernel module. |
| **ioctl** | "I/O Control" — a system call for sending custom commands to a driver. |
| **kprobe / kretprobe** | A kernel mechanism that lets you hook into any kernel function. We hook `vfs_write()` to auto-detect file writes. |
| **printk()** | The kernel's version of `printf()`. Messages go to `dmesg`. |
| **dmesg** | Shows the kernel's message log. Like a black box recorder. |
| **Circular buffer** | A fixed-size list where new entries overwrite old ones. Never grows. |
| **Sliding window** | "Look at the last N seconds." The window slides forward with time. |
| **Anomaly detection** | Spotting unusual patterns: "You usually write 1-2 files. Now you wrote 50 in 10 seconds!" |
| **DLP** | Data Loss Prevention — stopping sensitive data from leaving the organisation. |
| **PID** | Process ID — a number identifying a running program. |
| **Monotonic time** | A clock that only moves forward, never jumps. Immune to system clock changes. |
| **Atomic context** | A special kernel mode where you can't sleep. Requires trylock instead of regular lock. |
| **make** | A build tool. Compiles code according to rules in a `Makefile`. |
| **Kbuild** | The Linux kernel's build system. Used in `src_kernel/Makefile`. |

---

## Quick Reference Card

```bash
# Build
make all

# Load driver
sudo insmod src_kernel/usb_audit.ko

# Run monitor
sudo ./src_user/usb_monitor --interactive

# Run all automated tests
sudo ./scripts/test_all.sh

# Check kernel logs
dmesg | grep usb_audit

# Unload driver
sudo rmmod usb_audit

# Clean build files
make clean

# One-click everything
sudo ./scripts/run.sh

# Generate report
python3 scripts/generate_report.py
```

---

## FAQ

**Q: Why do I need `sudo`?**
A: Loading kernel modules and accessing `/dev` requires root privileges. Security feature — prevents random apps from injecting code into the kernel.

**Q: What's the difference between the C app and Python app?**
A: The C app talks directly to our kernel module via ioctl (dashboard). The Python app watches the filesystem independently using watchdog (background monitor). They work together.

**Q: What's a kprobe and why is it a big deal?**
A: A kprobe lets our driver hook into the kernel's own file-writing function. This means file writes are detected **automatically** — no app needs to report them. Our driver just knows.

**Q: Does this work on Windows/Mac?**
A: No. Kernel modules are Linux-specific. This targets the Raspberry Pi 4 running Linux.

**Q: Can I change the alert threshold without recompiling?**
A: Yes! Use `T 3 2000` in the monitor, or `-t 3 -w 2000` flags, or the SET_ANOMALY ioctl from any program.

**Q: What bugs did you fix during development?**
A: Several. A naming clash with the kernel's own `enable_kprobe()` function (renamed to `enable_vfs_kprobe`). A null-termination typo in the mount path. Inconsistent timestamps between the atomic and regular logging paths (both now use monotonic time). Missing FILE_DELETE tracking in the atomic path. An ioctl structure too large for the kernel's size field (worked around with a placeholder type).

---

*Still confused? That's OK — this is university-level OS material. Read through the code comments, run the system, play with it. Learning OS concepts takes hands-on experimentation.* 🧪

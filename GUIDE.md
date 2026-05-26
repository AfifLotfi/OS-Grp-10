# 🧠 The Absolute Beginner's Guide to Our USB File Transfer Activity Driver

---

> **Who is this for?** Anyone who looks at this project and thinks *"I have no idea what any of this means."*
>
> By the time you finish reading, you'll understand exactly what we built, why we built it, and how every piece fits together.

---

## 📖 Table of Contents

1. [What Problem Are We Solving?](#1-what-problem-are-we-solving)
2. [The Big Picture: How a Computer Runs Code](#2-the-big-picture-how-a-computer-runs-code)
3. [User-Space vs. Kernel-Space: The Two Worlds](#3-user-space-vs-kernel-space-the-two-worlds)
4. [What Is a "Driver" and Why Do We Need One?](#4-what-is-a-driver-and-why-do-we-need-one)
5. [Our Project: The Bird's-Eye View](#5-our-project-the-birds-eye-view)
6. [The Three Layers of Our System](#6-the-three-layers-of-our-system)
7. [File-by-File Walkthrough](#7-file-by-file-walkthrough)
8. [How to Build and Run It (Step by Step)](#8-how-to-build-and-run-it-step-by-step)
9. [How to Test the Mass-Copy Alert](#9-how-to-test-the-mass-copy-alert)
10. [Glossary: Jargon Buster](#10-glossary-jargon-buster)

---

## 1. What Problem Are We Solving?

Imagine you work at a company that handles sensitive data. An employee plugs in a USB thumb drive and starts copying hundreds of confidential files. How would you know? How would you stop it?

Our project is a **surveillance system for USB drives**. It watches every file that gets written to a USB stick and, if someone copies too many files too quickly (suspicious "mass-copy" behaviour), it **automatically raises an alarm**.

This is called **Data Loss Prevention (DLP)** — stopping sensitive data from walking out the door on a tiny USB stick.

---

## 2. The Big Picture: How a Computer Runs Code

Before we dive into our project, you need to understand the two "levels" at which code runs on a computer.

Think of a computer like a **restaurant**:

| Restaurant Analogy | Computer Equivalent |
|---|---|
| The **kitchen** — where food is prepared, stoves are controlled, inventory is managed. Only the chef has access. | The **kernel** — the core of the operating system. It controls the CPU, memory, and all hardware. |
| The **dining room** — where customers sit, order food, and eat. They can only see what the waiter brings them. | **User-space** — where your apps live (browser, text editor, games). Apps can't touch hardware directly. |
| The **waiter** — takes orders from the dining room to the kitchen and brings food back. | **System calls** — the mechanism that lets user apps ask the kernel to do things. |

**Key idea:** Your apps (user-space) can't just reach out and grab data from a USB stick. They have to *ask the kernel* to do it for them. The kernel is the boss of all hardware.

---

## 3. User-Space vs. Kernel-Space: The Two Worlds

```
┌─────────────────────────────────────────┐
│              USER-SPACE                  │
│  (Your apps: browser, VS Code, etc.)    │
│                                          │
│  ✅ Can: open files, print text, play   │
│         music, browse the web            │
│  ❌ Can't: talk to USB ports directly,  │
│          manage memory, control the CPU  │
├─────────────────────────────────────────┤
│             KERNEL-SPACE                 │
│  (The Linux kernel — the "brain")       │
│                                          │
│  ✅ Can: control ALL hardware, manage   │
│         memory, schedule processes       │
│  ✅ Has: absolute power over everything │
└─────────────────────────────────────────┘
```

**Why separate them?** Safety. If a buggy app crashes, it only crashes itself. If the kernel crashed, the whole computer would freeze. The wall between user-space and kernel-space protects the system.

---

## 4. What Is a "Driver" and Why Do We Need One?

A **driver** is a piece of kernel-space code that teaches the kernel how to talk to a specific piece of hardware.

| Without a driver | With a driver |
|---|---|
| You plug in a USB stick. The kernel sees "something" on the USB port but has no idea what it is or how to read files from it. | The USB storage driver kicks in and says "I know how to talk to this! Let me handle it." Now the kernel can read/write files. |

**We wrote a custom driver.** Not to *use* the USB stick (Linux already has that), but to **watch and log** every file operation happening on it. Think of it as a security camera that we installed *inside* the kernel.

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
4. Our driver logs the file name, size, and time
       │
       ▼
5. You copy 6 files in 3 seconds (suspicious!)
       │
       ▼
6. Our driver AUTOMATICALLY raises a SECURITY ALERT
       │
       ▼
7. A user app shows all the logs and alerts on screen
```

All of this is **logged permanently** in the kernel's message buffer (`dmesg`) and can be retrieved at any time.

---

## 6. The Three Layers of Our System

Our project has three layers working together:

### Layer 1: The Kernel Module (`usb_audit.ko`)
- Lives in **kernel-space**
- Created when we run `make` in `src_kernel/`
- Loaded into the kernel with `sudo insmod usb_audit.ko`
- Creates a "virtual file" at `/dev/usb_audit` that user apps can talk to
- Watches for USB devices being plugged in / unplugged
- Maintains a **circular buffer** (a fixed-size list that wraps around) of the last 128 events
- Runs the **anomaly detection engine** — automatically detects mass-copy bursts

### Layer 2: The User-Space C Application (`usb_monitor`)
- Lives in **user-space**
- A normal program you run from the terminal
- Opens `/dev/usb_audit` and talks to the kernel module using **ioctl** (a special kind of system call for drivers)
- Displays a dashboard with statistics, logs, and alerts
- Lets you inject test events to verify the system works

### Layer 3: The Python Watchdog (`file_tracker.py`)
- An alternative user-space monitor
- Uses the `watchdog` library to watch the USB mount folder in real time
- Has its own independent mass-copy detection
- Useful for demonstrations on the Raspberry Pi

```
┌──────────────────────────────────────────────────┐
│                  USER-SPACE                       │
│  ┌──────────────┐    ┌────────────────────────┐  │
│  │ usb_monitor  │    │   file_tracker.py      │  │
│  │  (C app)     │    │   (Python watchdog)    │  │
│  └──────┬───────┘    └───────────┬────────────┘  │
│         │ ioctl()                │ watchdog lib   │
│         ▼                        ▼                │
├──────────────────────────────────────────────────┤
│                KERNEL-SPACE                       │
│  ┌──────────────────────────────────────────┐    │
│  │         usb_audit.ko (our driver)        │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ │    │
│  │  │ USB      │ │ Circular │ │ Anomaly  │ │    │
│  │  │ Notifier │ │ Log Buf  │ │ Detector │ │    │
│  │  └──────────┘ └──────────┘ └──────────┘ │    │
│  └──────────────────────────────────────────┘    │
│                      │                            │
│                      ▼                            │
│              /dev/usb_audit                       │
│           (character device)                      │
└──────────────────────────────────────────────────┘
```

---

## 7. File-by-File Walkthrough

### `include/usb_tracker.h` — The "Contract"

This is a **header file** — it defines the data structures and commands that both the kernel module and the user app agree to use. Think of it as a *contract*: "If you send me this kind of data, I'll understand it."

**What it defines:**

| Concept | Plain English |
|---|---|
| `usb_audit_log_entry_t` | A single event record: "At time X, PID Y created file Z (size: 1024 bytes)" |
| `usb_audit_stats_t` | Running totals: "So far: 42 files created, 3,000,000 bytes written, 2 alerts" |
| `usb_audit_anomaly_t` | Anomaly config: "Alert if more than 5 files change within 3000 ms" |
| `USB_AUDIT_GET_STATS` | ioctl command: "Hey kernel, give me the current statistics" |
| `USB_AUDIT_SET_ANOMALY` | ioctl command: "Hey kernel, change the anomaly threshold to 10" |

### `src_kernel/usb_audit.c` — The Kernel Module (The Brain)

This is the most important file. It's written in C and runs **inside the Linux kernel**. Here's what each section does:

#### 📌 Module Registration
```c
module_init(usb_audit_init);
module_exit(usb_audit_exit);
```
When you type `sudo insmod usb_audit.ko`, the kernel calls `usb_audit_init()`. When you type `sudo rmmod usb_audit`, it calls `usb_audit_exit()`. These are the "on" and "off" switches.

#### 📌 Character Device Creation
The driver creates a **character device** (a special file at `/dev/usb_audit`). Unlike a regular file that stores data on disk, this "file" is a **pipe to our driver**. When a user app reads from it, they get log entries. When they write to it, they inject events.

#### 📌 USB Hotplug Notifier
```c
usb_register_notify(&usb_nb);
```
This tells the kernel: "Whenever a USB device is plugged in or unplugged, call my function `usb_audit_notify()`." Our function checks if it's a storage device and logs the event.

#### 📌 Circular Log Buffer
A **circular buffer** is a fixed-size array (128 slots) that wraps around. When full, the oldest entry gets overwritten. This prevents memory from growing forever.

```
Position:  0    1    2   ...  125  126  127
         ┌────┬────┬────┬───┬─────┬─────┬─────┐
         │ ev1│ ev2│ ev3│...│     │     │     │
         └────┴────┴────┴───┴─────┴─────┴─────┘
           ↑                        ↑
         tail (oldest)           head (next write)
```

#### 📌 Anomaly Detection Engine (The Secret Sauce)
This is the **advanced challenge** feature. Here's how it works:

1. Every time a file is created or modified, we record the **timestamp** in a 64-slot ring buffer.
2. After recording, we count: "How many timestamps in the ring are within the last 3 seconds?"
3. If the count is **more than 5**, we raise an alert.
4. A **cooldown** (5 seconds) prevents alert spam.

```
Timeline:
t=0.0  ──► CREATE file1.txt  (ring: [0.0])
t=0.4  ──► CREATE file2.txt  (ring: [0.0, 0.4])
t=0.8  ──► CREATE file3.txt  (ring: [0.0, 0.4, 0.8])
t=1.2  ──► CREATE file4.txt  (ring: [0.0, 0.4, 0.8, 1.2])
t=1.6  ──► CREATE file5.txt  (ring: [0.0, 0.4, 0.8, 1.2, 1.6])
t=2.0  ──► CREATE file6.txt  (ring: [0.0, 0.4, 0.8, 1.2, 1.6, 2.0])
                               ↑ 6 entries in 3s window → ALERT! 🚨
```

#### 📌 printk() Logging
```c
printk(KERN_INFO "[usb_audit] Event from PID %d: type=%d path=%s\n", ...);
```
`printk()` is the kernel's version of `printf()`. Messages go into the kernel's log buffer, which you can view with `dmesg`. This is how our driver leaves an audit trail.

### `src_user/usb_monitor.c` — The User-Space C App (The Dashboard)

This is a normal C program. It uses **ioctl** (I/O Control) to send commands to our driver through `/dev/usb_audit`.

**Key features:**
- **Interactive mode:** A menu where you type commands (`C /path/to/file` to simulate a file creation, `S` for stats, etc.)
- **Daemon mode:** A dashboard that refreshes every 2 seconds, showing live stats and logs
- **Auto-check:** After every file event, it asks the kernel "Did that trigger an alert?" and shows a warning banner if so

### `src_user/file_tracker.py` — The Python Watchdog

Uses the `watchdog` Python library to watch the actual USB mount folder on the Raspberry Pi. It detects real file operations and implements its own sliding-window anomaly detection.

### `scripts/run.sh` — The One-Click Launcher

A Bash script that does everything for you:
1. Checks you're running as root
2. Compiles the kernel module
3. Compiles the user app
4. Loads the module into the kernel
5. Verifies `/dev/usb_audit` exists
6. Launches the monitor
7. When you press Ctrl+C, it cleans everything up

Just run: `sudo ./scripts/run.sh`

### `Makefile` — The Build System

Tells the compiler how to turn our source code into runnable programs. `make all` builds everything; `make clean` removes build artifacts.

---

## 8. How to Build and Run It (Step by Step)

> ⚠️ **You must be on a Raspberry Pi 4 running Raspbian 64-bit** (or any Linux system with kernel headers installed).

### Step 1: Install the tools
```bash
sudo apt update
sudo apt install raspberrypi-kernel-headers build-essential -y
```

### Step 2: Build everything
```bash
cd OS-Grp-10
make all
```

This produces:
- `src_kernel/usb_audit.ko` — the kernel module
- `src_user/usb_monitor` — the user-space app

### Step 3: Load the driver
```bash
sudo insmod src_kernel/usb_audit.ko
```

Check it worked:
```bash
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
C test.txt
C test2.txt
C test3.txt
C test4.txt
C test5.txt
C test6.txt     ← This should trigger a SECURITY ALERT!
S               ← Show statistics
L               ← Show log entries
Q               ← Quit
```

### Step 6: Unload the driver
```bash
sudo rmmod usb_audit
```

### Or... Just Run the Script!
```bash
sudo ./scripts/run.sh --interactive
```

---

## 9. How to Test the Mass-Copy Alert

### Via the C app (interactive mode)
```
T 5 3000          ← Set threshold: 5 ops in 3000ms
C a.txt
C b.txt
C c.txt
C d.txt
C e.txt
C f.txt           ← ALERT! 🚨
```

### Via dmesg (kernel logs)
```bash
dmesg | grep "SECURITY ALERT"
# Output: [usb_audit] *** SECURITY ALERT *** Mass-copy detected! 6 file ops within 3000 ms (threshold=5)
```

### Custom thresholds
```bash
# Alert after just 3 files within 2 seconds:
sudo ./src_user/usb_monitor -i -t 3 -w 2000
```

---

## 10. Glossary: Jargon Buster

| Term | What It Actually Means |
|---|---|
| **Kernel** | The core of the operating system. The boss of all hardware. |
| **User-space** | Where normal applications run. Restricted access to hardware. |
| **Kernel module (.ko)** | A plugin for the kernel. You can load/unload it without rebooting. |
| **Driver** | Code that tells the kernel how to talk to hardware. |
| **Character device** | A virtual file (like `/dev/usb_audit`) that acts as a pipe between a user app and a driver. |
| **insmod** | "Insert Module" — loads a `.ko` file into the running kernel. |
| **rmmod** | "Remove Module" — unloads a kernel module. |
| **ioctl** | "I/O Control" — a system call that lets user apps send custom commands to a driver. |
| **printk()** | The kernel's version of `printf()`. Messages go to `dmesg`. |
| **dmesg** | A command that shows the kernel's message log. Like a black box recorder. |
| **Circular buffer** | A fixed-size list where new entries overwrite the oldest ones. Never grows infinitely. |
| **Sliding window** | A time-based filter: "Look at the last N seconds of data." The window slides forward as time passes. |
| **Anomaly detection** | Spotting unusual patterns. "You usually write 1-2 files. Now you wrote 50 in 10 seconds — that's suspicious!" |
| **DLP** | Data Loss Prevention — stopping sensitive data from leaving the organisation. |
| **PID** | Process ID — a number that uniquely identifies a running program. |
| **make** | A build tool that compiles your code according to rules in a `Makefile`. |
| **Kbuild** | The Linux kernel's custom build system. Used in `src_kernel/Makefile`. |

---

## 🎯 Quick Reference Card

```bash
# Build
make all

# Load driver
sudo insmod src_kernel/usb_audit.ko

# Run monitor
sudo ./src_user/usb_monitor --interactive

# Check kernel logs
dmesg | grep usb_audit

# Unload driver
sudo rmmod usb_audit

# Clean build files
make clean

# One-click everything
sudo ./scripts/run.sh
```

---

## ❓ FAQ

**Q: Why do I need `sudo` for everything?**
A: Loading kernel modules and accessing `/dev` devices requires root (administrator) privileges. This is a security feature — you don't want random apps injecting code into the kernel.

**Q: What's the difference between the C app and the Python app?**
A: The C app talks directly to our kernel module via ioctl. The Python app watches the filesystem independently using the `watchdog` library. They're two different approaches to the same goal.

**Q: Does this work on Windows/Mac?**
A: No. Kernel modules are Linux-specific. Windows and macOS have completely different driver architectures. This project targets the Raspberry Pi 4 running Linux.

**Q: What if I don't have a Raspberry Pi?**
A: You can compile and test on any Linux machine (Ubuntu, Debian, etc.) as long as you have the kernel headers installed. The USB notifier won't detect real USB devices on a VM, but the character device and anomaly detection will work fine.

**Q: Can I change the alert threshold without recompiling?**
A: Yes! Use the `T` command in interactive mode, or the `-t` / `-w` CLI flags, or the `USB_AUDIT_SET_ANOMALY` ioctl directly from your own code.

---

*Still confused? That's OK — this is 3rd-year university material. Read through the code comments (they're very detailed), run the system, play with it, and things will click. Learning OS concepts takes time and hands-on experimentation.* 🧪

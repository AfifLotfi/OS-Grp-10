# Group 10 — Presentation Role Assignments

> **Project 15:** USB File Transfer Activity Driver
> **Course:** CSC1107 — Operating Systems
> **Format:** 8–12 minute group video — every member speaks and demonstrates their code

---

## Presentation Flow Overview

| Order | Member | Topic | Est. Time |
|---|---|---|---|
| 1 | Member 1 | Project Overview & System Architecture | 2 min |
| 2 | Member 2 | Kernel Module — Core Driver, Logging & kprobe | 2.5 min |
| 3 | Member 3 | Kernel Module — USB Monitoring, ioctl API & Event Handling | 2 min |
| 4 | Member 4 | Anomaly Detection Engine & User-Space C Application | 2.5 min |
| 5 | Member 5 | Python Watchdog, Build System & Live Integration Demo | 2.5 min |

> **Total:** ~11.5 minutes (within the 8–12 minute requirement)

---

---

## Member 1 — Project Overview & System Architecture

### What You Are Presenting

You set the stage. You explain **what** we built, **why** it matters, and **how** the pieces fit together at a high level. This is the "big picture" that gives context to everything that follows.

### Key Talking Points

**1. The Problem (30 seconds)**
- Imagine a company with sensitive data. An employee plugs in a USB stick and starts copying files. How would anyone know?
- This is **Data Loss Prevention (DLP)** — stopping data from walking out on a USB drive.
- Our solution: a surveillance system for USB storage devices that watches, logs, and alerts.

**2. What We Built (45 seconds)**
- A **Linux kernel module** (`usb_audit.ko`) that lives inside the operating system.
- It monitors USB storage devices at two levels:
  - **Device level:** detects when a USB drive is plugged in or removed (hotplug).
  - **File level:** tracks every file created, modified, or deleted on the USB drive.
- A **user-space C application** (`usb_monitor`) that shows a live dashboard with statistics, logs, and alerts.
- A **Python watchdog** (`file_tracker.py`) that watches folders in real time and reports events to the kernel.
- An **automated test suite** (`test_all.sh`) that verifies all 22 features in one command.

**3. System Architecture (45 seconds)**
- Show the architecture diagram from `GUIDE.md` or draw it on screen.
- Explain the two worlds:
  - **Kernel-space:** our driver has full hardware access. It creates `/dev/usb_audit` — a virtual file that acts as a pipe between apps and the driver.
  - **User-space:** the C monitor and Python script talk to the driver through this pipe using `open()`, `write()`, and `ioctl()`.
- **Key feature — the kprobe:** our driver hooks into the kernel's own `vfs_write()` function. This means file writes are detected **automatically** — no app needs to report them. The driver just knows.
- Two event paths feed into one detection engine:
  - **Path A (automatic):** kprobe detects write → logs event.
  - **Path B (user-reported):** app notices change → sends event to `/dev/usb_audit`.

**4. The Shared Contract (30 seconds)**
- Show `include/usb_tracker.h` — this header file is the "contract" between kernel and user code.
- It defines event types (DEVICE_IN, FILE_CREATE, FILE_MODIFY, FILE_DELETE, ALERT), data structures for log entries and statistics, and seven ioctl commands.
- Both sides include the same file, so they always agree on data formats.
- Mention an interesting design challenge we solved: the GET_LOGS structure is 35 KB, which is too large for the kernel's ioctl size field. We used a placeholder type in the macro definition as a workaround.

### Files to Show On Screen

| File | What to Point Out |
|---|---|
| `README.md` | Project overview, features table |
| `GUIDE.md` | Architecture diagram, layers explanation |
| `include/usb_tracker.h` | ioctl commands, struct definitions, the GET_LOGS workaround comment |

### Demo Actions (30 seconds)

1. Show the project directory tree: `ls -R ~/OS-Grp-10`
2. Walk through each folder briefly: `include/` (shared header), `src_kernel/` (driver), `src_user/` (apps), `scripts/` (automation).
3. Show the architecture diagram (pull up `GUIDE.md`).

### Transition Line

> *"Now that you understand the big picture, Member 2 will dive into the kernel module — the brain of our system — and show you exactly how it initialises and how our kprobe automatically detects file writes."*

---

---

## Member 2 — Kernel Module: Core Driver, Logging & kprobe Interception

### What You Are Presenting

You explain the **heart of the system** — the kernel module. You cover how it starts up, how it creates the device node, how it logs events, and the advanced kprobe feature that makes our driver autonomous.

### Key Talking Points

**1. What Is a Kernel Module? (30 seconds)**
- A kernel module (`.ko` file) is a plugin for the Linux kernel. You can load and unload it without rebooting.
- `insmod` loads it; `rmmod` unloads it.
- Our module is called `usb_audit.ko`. Once loaded, it creates the device file `/dev/usb_audit`.

**2. Module Initialisation — 7 Steps (60 seconds)**
- Walk through `usb_audit_init()` in `src_kernel/usb_audit.c`:
  1. **Allocate device number:** `alloc_chrdev_region()` asks the kernel for a major number.
  2. **Register character device:** `cdev_init()` + `cdev_add()` register our device with the kernel.
  3. **Create /dev node:** `class_create()` + `device_create()` make `/dev/usb_audit` appear. We use `#if LINUX_VERSION_CODE >= KERNEL_VERSION(6,4,0)` because `class_create()` changed its signature — our driver works on both old and new kernels.
  4. **Allocate log buffer:** `kmalloc_array()` creates a 128-entry circular buffer.
  5. **Initialise stats:** Zero all counters and the anomaly detection ring.
  6. **Register USB notifier:** Tell the kernel to call us when USB devices change.
  7. **Register kprobe:** Hook into `vfs_write()` for automatic file write detection.
- If any step fails, `goto` unwinds in reverse order — standard kernel practice.
- The module parameter `enable_vfs_kprobe` (renamed from `enable_kprobe` to avoid a naming clash with the kernel's own function) lets you disable the kprobe at load time.

**3. kprobe — Automatic File Write Interception (45 seconds)**
- This is one of the most advanced features of our project.
- A **kretprobe** (kernel return probe) hooks into the Linux kernel's own `vfs_write()` function — the function that EVERY file write on the system goes through.
- It has two parts:
  - **Entry handler:** Saves the file pointer and the number of bytes being written.
  - **Return handler:** After the write completes, checks if the file is on our monitored USB path. If yes → logs the event with the actual byte count.
- **The atomic context challenge:** kprobe handlers run in a special mode where they CANNOT sleep. Regular `mutex_lock()` can sleep, so it would crash the kernel.
- **Our solution:** We wrote a separate logging function (`audit_log_event_atomic`) that uses `mutex_trylock()` — it either grabs the lock instantly or skips the event. Safe, no crashes.
- **Timestamp consistency fix:** Both the atomic kprobe path and the regular user-space path now use `ktime_get_ns()` (monotonic time). They used to use different clock sources, which would have made timestamps inconsistent.

**4. The Circular Log Buffer (30 seconds)**
- A fixed-size array of 128 entries. A `head` pointer marks the next write position.
- When full, the oldest entry gets overwritten — no infinite memory growth.
- The `read()` handler returns entries one at a time and properly advances `f_pos`.
- `log_count` tracks how many valid entries exist.

**5. Error Handling (15 seconds)**
- Every function returns 0 on success, negative errno on failure.
- `printk()` messages at KERN_INFO, KERN_WARNING, and KERN_ERR levels — all visible via `dmesg`.

### Files to Show On Screen

| File | What to Point Out |
|---|---|
| `src_kernel/usb_audit.c` | `usb_audit_init()` (the 7 steps), `audit_log_event_atomic()`, `krp_vfs_write_ret()`, circular buffer logic, `audit_log_event()` |

### Demo Actions (45 seconds)

1. **Build:** `make kernel` — show it compiles with zero errors and zero warnings.
2. **Load:** `sudo insmod src_kernel/usb_audit.ko`
3. **Verify:** `lsmod | grep usb_audit` → shows module is loaded.
4. **Device node:** `ls -la /dev/usb_audit` → shows the character device.
5. **Kernel log:** `dmesg | tail -15` → point out:
   - `[usb_audit] Initialising USB File Transfer Activity Driver`
   - `[usb_audit] Allocated major 236, minor 0`
   - `[usb_audit] kretprobe on vfs_write registered — kernel-level file write interception ACTIVE` ← highlight this!
   - `[usb_audit] USB hotplug notifier registered`
   - `[usb_audit] Driver loaded successfully`
6. **Unload:** `sudo rmmod usb_audit` → show clean shutdown in dmesg.

### Transition Line

> *"You've seen how the driver starts up and how the kprobe automatically detects writes. Now Member 3 will show you how the driver detects USB devices being plugged in, and how user-space apps talk to it through the ioctl interface."*

---

---

## Member 3 — Kernel Module: USB Monitoring, ioctl API & Event Handling

### What You Are Presenting

You cover how the driver detects real USB hardware events and how it communicates with user-space applications through the ioctl protocol and read/write operations.

### Key Talking Points

**1. USB Hotplug Detection (45 seconds)**
- The kernel has a **notifier chain** — a list of functions to call when USB devices change.
- `usb_register_notify(&usb_nb)` adds our callback to that chain.
- Our callback `usb_audit_notify()` checks `bDeviceClass`:
  - `USB_CLASS_MASS_STORAGE (0x08)` → it's a storage device!
  - Also accepts `0x00` (per-interface class) since many USB drives report class at the interface level.
- On `USB_DEVICE_ADD` → logs DEVICE_IN with vendor ID, product ID, and product name.
- On `USB_DEVICE_REMOVE` → logs DEVICE_OUT.

**2. The ioctl Command Dispatcher (60 seconds)**
- **ioctl** = "I/O Control" — a system call for sending custom commands to a driver.
- Our driver uses magic number `'U'` (0x55) to identify its commands.
- `usb_audit_ioctl()` validates the magic number and dispatches to the right handler.
- Seven commands are supported:

| Command | What It Does |
|---|---|
| `GET_STATS (1)` | Returns all counters: bytes written, files created/modified/deleted, device events, alerts |
| `CLEAR_LOGS (2)` | Empties the circular log buffer |
| `SET_PATH (3)` | Sets which USB mount path to monitor (for kprobe filtering) |
| `GET_LOGS (4)` | Returns up to N recent log entries (oldest to newest) |
| `RESET_STATS (5)` | Zeros all counters AND clears the anomaly detection ring |
| `SET_ANOMALY (6)` | Configures the anomaly threshold and time window |
| `GET_ANOMALY (7)` | Returns current burst count and whether an alert is active |

- Every handler uses `copy_to_user()` / `copy_from_user()` to safely transfer data across the kernel/user boundary.

**3. The Write Handler — How Events Get In (30 seconds)**
- User-space sends a string like: `C /media/usb/file.txt (1024 bytes)\n`
- The write handler parses it:
  - First character = event code (C=create, M=modify, D=delete, A=alert)
  - Everything after whitespace = file path
  - Optional `(N bytes)` suffix at the end → parsed with `strrchr()` + `sscanf()`
- **Bug fix we made:** events without a size suffix used to be silently dropped because `audit_log_event()` was nested inside an `if(paren)` block. Now all events are logged — size just defaults to 0 if not provided.

**4. The Read Handler — How Events Get Out (15 seconds)**
- Returns the oldest log entry from the circular buffer.
- Returns 0 (EOF) when no entries are available.
- Properly advances `f_pos` so repeated reads work correctly.

**5. File Size Tracking — End to End (15 seconds)**
- User-space sends real file sizes via the event string format.
- The kprobe captures the actual `vfs_write` return value (bytes written).
- Both paths store the size in `entry->file_size` and add it to `stats.total_bytes_written`.
- Statistics show real, accurate byte counts.

### Files to Show On Screen

| File | What to Point Out |
|---|---|
| `src_kernel/usb_audit.c` | `usb_audit_notify()`, `usb_audit_ioctl()`, `usb_audit_write()`, `usb_audit_read()` |
| `include/usb_tracker.h` | The 7 ioctl command macros, the stats/log structs |

### Demo Actions (45 seconds)

1. **USB hotplug:** Have the USB drive unplugged. Start `dmesg -w` in one terminal. Plug it in → show DEVICE_IN appears. Unplug → show DEVICE_OUT.
2. **Monitor:** Launch `sudo ./src_user/usb_monitor -p "/media/pi/USB"`
3. **Inject events:**
   ```
   C /media/pi/USB/doc.pdf     → shows "Sent event"
   M /media/pi/USB/data.txt    → shows "Sent event"
   D /media/pi/USB/old.txt     → shows "Sent event"
   ```
4. **Show stats:** `S` → point out Files created=1, Files modified=1, Files deleted=1.
5. **Show logs:** `L` → point out the timestamps, PIDs, and event types.
6. **Clear and reset:** `X` then `R` then `S` → show everything back to zero.

### Transition Line

> *"You've seen how events flow in and out of the driver. Now Member 4 will show you the most exciting part — the anomaly detection engine that automatically spots mass-copy attacks, and the C dashboard that makes it all visible."*

---

---

## Member 4 — Anomaly Detection Engine & User-Space C Application

### What You Are Presenting

You explain the **advanced challenge feature** — the automatic mass-copy detection engine — and the C application that lets users interact with the whole system.

### Key Talking Points

**1. The Anomaly Detection Problem (20 seconds)**
- Goal: automatically detect when someone copies too many files too quickly to a USB drive.
- Like a speed camera: count operations within a time window, raise alarm if too many.
- Fully automatic — no human watching needed.

**2. How the Kernel Engine Works (60 seconds)**
- **Ring buffer:** 64-entry array of timestamps (`ktime_t`).
- Every FILE_CREATE or FILE_MODIFY records its timestamp.
- After recording, the engine counts: "How many timestamps are within the sliding window?"
- Default window: 3000 ms (3 seconds). Default threshold: 5 operations.
- **Cooldown:** 5000 ms (5 seconds) between alerts — prevents spam during sustained copy operations.
- When triggered: automatically writes an ALERT log entry into the circular buffer AND calls `printk(KERN_WARNING)` so it appears in `dmesg`.
- Both the kprobe path (automatic) and the user-space path (injected) feed into the SAME engine.
- Both paths use `ktime_get_ns()` (monotonic time) for consistent timestamps.

**3. Configuration at Runtime (30 seconds)**
- Everything is configurable without recompiling:
  - `T 3 2000` in the interactive monitor.
  - `-t 3 -w 2000` command-line flags.
  - `USB_AUDIT_SET_ANOMALY` ioctl from any program.
- `USB_AUDIT_GET_ANOMALY` ioctl returns current burst count and alert status.

**4. Three-Layer Detection (20 seconds)**
- **Kernel layer:** `anomaly_check_burst()` — automatic, always running.
- **User-space layer:** C monitor polls `GET_ANOMALY` after every event.
- **Python layer:** `file_tracker.py` has its own sliding window.
- If ANY layer detects a burst, the alert is visible. Redundancy ensures coverage.

**5. The C Application — usb_monitor (45 seconds)**
- ~530 lines of C, communicates via ioctl on `/dev/usb_audit`.
- **Interactive mode:** 11 commands:
  - `C/M/D` — inject file events (with file size in the event string)
  - `A` — manually trigger alert
  - `T n ms` — configure anomaly detection
  - `S` — show statistics
  - `L` — show recent logs
  - `R` — reset counters + anomaly ring
  - `X` — clear log buffer
  - `Q` — quit
- **Daemon mode** (`-d`): dashboard refreshes every 2 seconds.
- **Auto-check:** after every event, queries kernel anomaly status and displays SECURITY ALERT banner if triggered.
- **CLI flags:** `-p` path, `-t` threshold, `-w` window, `-i` interactive, `-d` daemon.
- **Bug fix:** the mount path was not properly null-terminated (a multi-character literal typo). Fixed to ensure the path is always a valid C string.

### Files to Show On Screen

| File | What to Point Out |
|---|---|
| `src_kernel/usb_audit.c` | `anomaly_check_burst()`, the cooldown logic, the ALERT entry creation |
| `src_user/usb_monitor.c` | `interactive_menu()`, `set_anomaly_thresholds()`, `send_event()`, `check_anomaly_status()` |

### Demo Actions (60 seconds)

**This is the most dramatic demo — practise it well!**

1. **Launch monitor:** `sudo ./src_user/usb_monitor -p "/media/pi/USB"`
2. **Lower threshold:** `T 2 5000` (alert after just 3 file ops in 5 seconds).
3. **Trigger the alert live:**
   ```
   C /media/usb/a.txt     ← wait ~0.5s
   C /media/usb/b.txt     ← wait ~0.5s
   C /media/usb/c.txt     ← BAM! 🚨
   ```
4. **Show the red SECURITY ALERT banner** on screen — pause for effect.
5. **Verify kernel side:** `dmesg | grep "SECURITY ALERT"` → shows the same alert with burst details.
6. **Show stats:** `S` → alert_count is now 1.
7. **Show daemon mode:** quit and relaunch with `sudo ./src_user/usb_monitor -d` → show the live-refreshing dashboard.

### Transition Line

> *"You've seen the anomaly detection in action. Now Member 5 will show you the Python watchdog, how our build system ties everything together, and our automated test suite that proves everything works."*

---

---

## Member 5 — Python Watchdog, Build System, Testing & Live Integration Demo

### What You Are Presenting

You cover the Python alternative monitor, the build and automation pipeline, the automated test suite that validates everything, and wrap up with the conclusion. This is the "everything working together" finale.

### Key Talking Points

**1. The Python Watchdog — file_tracker.py (45 seconds)**
- Uses the `watchdog` library to monitor a folder in real time.
- Unlike the C monitor (interactive), this runs in the background automatically.
- **Four event handlers:**
  - `on_created()` — new file appears → sends "C" event with real file size from `os.path.getsize()`.
  - `on_modified()` — file being written → tracks growing size.
  - `on_closed()` — write finished → sends "M" event with final size.
  - `on_deleted()` — file removed → sends "D" event with size 0.
- **send_kernel_event():** Opens `/dev/usb_audit`, writes the formatted event string, closes it. If the kernel module isn't loaded, catches the error and continues — dual-mode operation.
- Has its own sliding-window anomaly detector (5 ops in 3 seconds) as a backup layer.

**2. Build System — Makefile (30 seconds)**
- **Top-level Makefile:** Three targets — `all` (kernel + user), `kernel`, `user`, `clean`.
- `make kernel` delegates to `src_kernel/Makefile` which uses the Linux Kbuild system (`obj-m := usb_audit.o`).
- `make user` compiles `usb_monitor.c` with `gcc -Wall -Wextra -O2`.
- Automatically finds kernel headers via `/lib/modules/$(uname -r)/build`.

**3. Automation Script — run.sh (30 seconds)**
- One command does everything: `sudo ./scripts/run.sh`
- Checks root privileges and kernel headers.
- Builds both components.
- Loads the kernel module.
- Verifies `/dev/usb_audit` exists.
- Shows recent kernel logs.
- Launches the monitor.
- On Ctrl+C: trap handler kills the monitor process and unloads the module.
- Colour-coded output (green = OK, yellow = warning, red = error).

**4. Automated Test Suite — test_all.sh (45 seconds)**
- **22 automated tests across 10 categories.**
- One command: `sudo ./scripts/test_all.sh`
- Tests everything: module loading, device node, kprobe status, notifier, monitor connection, event injection (C/M/D), statistics counters, log buffer, anomaly detection trigger, real USB drive I/O, clean shutdown.
- Resets statistics between tests for clean verification.
- Handles edge cases: pre-loaded module, module in use.
- **Verified result on our Pi: 22/22 passed.**

**5. Report Generation — generate_report.py (15 seconds)**
- Generates the Word document report using the `python-docx` library.
- No hand-crafted XML — just clean Python code calling `doc.add_paragraph()` and `doc.add_heading()`.
- Output: `Px_Group10-report-CSC1107.docx` with proper Calibri fonts, blue headings, styled tables, and code blocks.

**6. Conclusion — What We Achieved (30 seconds)**
- Complete Linux character device driver with full ioctl API.
- kprobe-based automatic file write interception — no user-space help needed.
- Configurable sliding-window anomaly detector with cooldown.
- End-to-end file size tracking with real byte counts.
- Three-layer anomaly detection for maximum coverage.
- Linux 6.4+ compatibility.
- Automated test suite with 22/22 tests passing.
- Real hardware validation on Raspberry Pi 4 with USB drive.
- One-command build and deployment.

### Files to Show On Screen

| File | What to Point Out |
|---|---|
| `src_user/file_tracker.py` | Event handlers, `send_kernel_event()`, anomaly detection |
| `Makefile` | The three targets: all, kernel, user |
| `src_kernel/Makefile` | `obj-m := usb_audit.o`, KDIR |
| `scripts/run.sh` | The trap handler, the step-by-step flow |
| `scripts/test_all.sh` | The 10 test categories, pass/fail reporting |
| `scripts/generate_report.py` | python-docx usage, clean API |

### Demo Actions (60 seconds)

1. **Show the Makefile in action:**
   ```bash
   make clean && make all
   ```
   → point out zero errors, zero warnings.

2. **Run the automated test suite (the star of this section):**
   ```bash
   sudo ./scripts/test_all.sh
   ```
   → scroll through the output, highlight `22 / 22 tests passed` and `ALL TESTS PASSED`.

3. **Python watchdog demo:**
   - Edit `USB_TARGET_PATH` in `file_tracker.py` if needed.
   - Launch: `python3 src_user/file_tracker.py`
   - In another terminal, create files on the USB drive:
     ```bash
     for i in $(seq 1 8); do echo "data$i" > /media/pi/USB/test_$i.txt; sleep 0.3; done
     ```
   - Show `[SECURITY ALERT]` appearing in the Python terminal.

4. **Show the one-click run.sh:**
   ```bash
   sudo ./scripts/run.sh
   ```
   → show it checking, building, loading, and launching. Press Ctrl+C → show the cleanup working.

5. **Closing statement:** summarise what we built and why it matters.

### Transition Line (Closing)

> *"That's our USB File Transfer Activity Driver. A complete Linux kernel module with automatic anomaly detection, a user-space dashboard, a Python watchdog, and an automated test suite — all verified on real hardware. Thank you for watching."*

---

---

## Presentation Tips

| Tip | Detail |
|---|---|
| **Timing** | Each member ~2 minutes. Total ~11.5 minutes. Practise with a stopwatch. |
| **Transitions** | Use the suggested transition lines or write your own. Smooth handoffs keep the video flowing. |
| **Code on screen** | Always show the relevant file while explaining it. Zoom in so the code is readable. |
| **Live demos** | Practise demos at least 3 times before recording. Have a backup screenshot if something fails. |
| **Speak naturally** | Do NOT read from the report or these notes word-for-word. Explain concepts in your own words — it sounds more authentic. |
| **Be visible** | Every member must appear on camera at some point. Switch between face cam and screen share. |
| **dmesg is your friend** | After every demo, show `dmesg \| tail -5` to prove the kernel is logging everything. |
| **Highlight the kprobe** | The kprobe feature is our most impressive technical achievement — make sure it gets emphasis. |
| **End with test_all.sh** | The automated test suite is a powerful closer — it proves everything works in one shot. |

---

## Quick Reference: Who Does What

| Member | Primary Files | Key Feature to Demo |
|---|---|---|
| 1 | `README.md`, `GUIDE.md`, `usb_tracker.h` | Architecture diagram, directory walkthrough |
| 2 | `usb_audit.c` (init, kprobe, logging) | `insmod` → dmesg showing kprobe active |
| 3 | `usb_audit.c` (notifier, ioctl, write/read) | USB hotplug + interactive event injection |
| 4 | `usb_audit.c` (anomaly), `usb_monitor.c` | Live SECURITY ALERT trigger (T 2 5000 demo) |
| 5 | `file_tracker.py`, `Makefile`, `run.sh`, `test_all.sh` | test_all.sh 22/22 + Python mass-copy demo |

---

*Group 10 — CSC1107 Operating Systems — Project 15*

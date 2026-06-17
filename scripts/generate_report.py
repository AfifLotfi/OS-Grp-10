#!/usr/bin/env python3
"""
generate_report.py — Professional Word Report Generator (Zero Dependencies)

Generates a fully formatted .docx report for the USB File Transfer Activity
Driver project using ONLY Python's standard library.  A .docx file is simply
a ZIP of XML files — we build those XML files directly.

Output: scripts/Px_Group10-report-CSC1107.docx
"""

import zipfile
import os
import datetime

OUTPUT_PATH = os.path.join(os.path.dirname(__file__),
                           "Px_Group10-report-CSC1107.docx")

# ── XML Templates ──────────────────────────────────────────────────────

XML_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

XML_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

XML_WORD_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""


def make_styles_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:pPr>
      <w:spacing w:before="400" w:after="200"/>
      <w:outlineLvl w:val="0"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
      <w:b/>
      <w:sz w:val="36"/>
      <w:color w:val="1F4E79"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:pPr>
      <w:spacing w:before="300" w:after="150"/>
      <w:outlineLvl w:val="1"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
      <w:b/>
      <w:sz w:val="28"/>
      <w:color w:val="2E75B6"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:pPr>
      <w:spacing w:before="200" w:after="100"/>
      <w:outlineLvl w:val="2"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
      <w:b/>
      <w:sz w:val="24"/>
      <w:color w:val="2E75B6"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Code">
    <w:name w:val="Code"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr>
      <w:spacing w:before="60" w:after="60"/>
      <w:shd w:fill="F2F2F2" w:val="clear"/>
      <w:ind w:left="360" w:right="360"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>
      <w:sz w:val="18"/>
      <w:color w:val="333333"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
      <w:sz w:val="22"/>
      <w:color w:val="333333"/>
    </w:rPr>
    <w:pPr>
      <w:spacing w:after="120" w:line="276" w:lineRule="auto"/>
    </w:pPr>
  </w:style>
  <w:style w:type="character" w:styleId="Strong">
    <w:name w:val="Strong"/>
    <w:rPr><w:b/></w:rPr>
  </w:style>
</w:styles>"""


def xml_escape(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))


class DocBuilder:
    """Builds a .docx document body using WordprocessingML XML."""

    def __init__(self):
        self.parts = []

    def _p(self, style, text, bold_runs=None):
        """Add a paragraph with optional bold segments."""
        self.parts.append(f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr>')
        if bold_runs:
            for is_bold, segment in bold_runs:
                seg = xml_escape(segment)
                if is_bold:
                    self.parts.append(f'<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">{seg}</w:t></w:r>')
                else:
                    self.parts.append(f'<w:r><w:t xml:space="preserve">{seg}</w:t></w:r>')
        elif text:
            self.parts.append(f'<w:r><w:t xml:space="preserve">{xml_escape(text)}</w:t></w:r>')
        self.parts.append('</w:p>')

    def h1(self, text):
        self._p("Heading1", text)

    def h2(self, text):
        self._p("Heading2", text)

    def h3(self, text):
        self._p("Heading3", text)

    def para(self, text):
        self._p("Normal", text)

    def bold_para(self, segments):
        """segments: list of (is_bold: bool, text: str)."""
        self._p("Normal", "", bold_runs=segments)

    def code(self, text):
        self._p("Code", text)

    def bullet(self, text):
        self.parts.append('<w:p><w:pPr><w:pStyle w:val="Normal"/>'
                          '<w:ind w:left="720" w:hanging="360"/>'
                          '<w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol"/></w:rPr>'
                          '</w:pPr>'
                          f'<w:r><w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol"/></w:rPr>'
                          f'<w:t xml:space="preserve">\u2022 </w:t></w:r>'
                          f'<w:r><w:t xml:space="preserve">{xml_escape(text)}</w:t></w:r>'
                          '</w:p>')

    def table(self, headers, rows):
        """Simple table with header row."""
        self.parts.append('<w:tbl><w:tblPr>'
                          '<w:tblW w:w="9000" w:type="dxa"/>'
                          '<w:tblBorders>'
                          '<w:top w:val="single" w:sz="4" w:space="0" w:color="2E75B6"/>'
                          '<w:left w:val="single" w:sz="4" w:space="0" w:color="2E75B6"/>'
                          '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="2E75B6"/>'
                          '<w:right w:val="single" w:sz="4" w:space="0" w:color="2E75B6"/>'
                          '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
                          '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
                          '</w:tblBorders></w:tblPr><w:tblGrid>')
        for _ in headers:
            self.parts.append('<w:gridCol w:w="2250"/>')
        self.parts.append('</w:tblGrid>')

        # Header row
        self.parts.append('<w:tr>')
        for h in headers:
            self.parts.append(
                '<w:tc><w:tcPr><w:shd w:fill="2E75B6" w:val="clear"/></w:tcPr>'
                f'<w:p><w:pPr><w:spacing w:after="40"/></w:pPr>'
                f'<w:r><w:rPr><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="20"/></w:rPr>'
                f'<w:t xml:space="preserve">{xml_escape(h)}</w:t></w:r></w:p></w:tc>')
        self.parts.append('</w:tr>')

        # Data rows
        for row in rows:
            self.parts.append('<w:tr>')
            for cell in row:
                self.parts.append(
                    '<w:tc><w:tcPr><w:shd w:fill="F7F9FC" w:val="clear"/></w:tcPr>'
                    f'<w:p><w:pPr><w:spacing w:after="40"/></w:pPr>'
                    f'<w:r><w:rPr><w:sz w:val="20"/></w:rPr>'
                    f'<w:t xml:space="preserve">{xml_escape(cell)}</w:t></w:r></w:p></w:tc>')
            self.parts.append('</w:tr>')
        self.parts.append('</w:tbl>')
        self.parts.append('<w:p/>')

    def page_break(self):
        self.parts.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

    def build(self):
        return ''.join(self.parts)


def build_document():
    d = DocBuilder()

    # ── Title Page ──
    d.parts.append('<w:p><w:pPr><w:spacing w:before="2400"/></w:pPr></w:p>')
    d._p("Heading1", "USB File Transfer Activity Driver")
    d._p("Heading2", "Design Documentation & Technical Report")
    d.para("")
    d.bold_para([(True, "Project: "), (False, "Project 15 — USB File Transfer Activity Driver")])
    d.bold_para([(True, "Course: "), (False, "CSC1107 — Operating Systems")])
    d.bold_para([(True, "Group: "), (False, "Group 10")])
    d.bold_para([(True, "Target Platform: "), (False, "Raspberry Pi 4, Raspbian 64-bit (Linux Kernel 6.x)")])
    d.bold_para([(True, "Date: "), (False, datetime.date.today().strftime("%d %B %Y"))])
    d.page_break()

    # ── Table of Contents placeholder ──
    d.h1("Table of Contents")
    d.para("1. Executive Summary")
    d.para("2. System Architecture & Design")
    d.para("3. Design Step-by-Step: Building the Driver")
    d.para("4. Kernel Module — Detailed Design")
    d.para("5. User-Space Application — Detailed Design")
    d.para("6. Python Watchdog Monitor")
    d.para("7. Anomaly Detection Engine")
    d.para("8. Build System & Automation")
    d.para("9. Communication Protocol (ioctl API)")
    d.para("10. Testing & Verification")
    d.para("11. Conclusion")
    d.page_break()

    # ── 1. Executive Summary ──
    d.h1("1. Executive Summary")
    d.para(
        "This project implements a Linux kernel module driver that monitors file transfer "
        "activity to removable USB storage devices. The system is designed for data loss "
        "prevention (DLP), cybersecurity auditing, and secure storage use cases. It runs "
        "on a Raspberry Pi 4 with Raspbian 64-bit."
    )
    d.para(
        "The solution consists of three integrated layers: (1) a kernel-space character "
        "device driver (usb_audit.ko) that intercepts USB device events and maintains an "
        "audit trail, (2) a user-space C application (usb_monitor) that communicates with "
        "the driver via ioctl system calls to display statistics and logs, and (3) a Python "
        "watchdog daemon (file_tracker.py) for alternative real-time filesystem monitoring."
    )
    d.para(
        "The advanced challenge goal — automatic mass-copy anomaly detection — is fully "
        "implemented in the kernel module with a configurable sliding-window burst detector "
        "that raises security alerts when file operations exceed a threshold within a time window."
    )

    # ── 2. System Architecture ──
    d.h1("2. System Architecture & Design")
    d.h2("2.1 High-Level Architecture")
    d.para(
        "The system follows a layered architecture separating user-space from kernel-space. "
        "The kernel module runs with full privileges and has direct access to USB and block "
        "device subsystems. The user-space applications communicate with the kernel module "
        "through a character device node (/dev/usb_audit) using standard file operations "
        "(open, read, write, ioctl)."
    )

    d.table(
        ["Layer", "Component", "Language", "Privilege Level"],
        [
            ["User-Space", "usb_monitor (C)", "C", "User (root for /dev access)"],
            ["User-Space", "file_tracker.py", "Python 3", "User"],
            ["Kernel-Space", "usb_audit.ko", "C (Kernel)", "Kernel (Ring 0)"],
        ]
    )

    d.h2("2.2 Data Flow")
    d.para(
        "When a file is written to a USB storage device: (1) The user-space application "
        "detects the file operation and sends an event string to /dev/usb_audit via write(). "
        "(2) The kernel module's write handler parses the event, records it in the circular "
        "log buffer, updates aggregate statistics, and feeds the anomaly detection engine. "
        "(3) If the anomaly threshold is exceeded, an alert is automatically logged with "
        "printk() for dmesg visibility. (4) The user app retrieves logs and statistics via "
        "ioctl() calls for display."
    )

    d.h2("2.3 Concurrency Model")
    d.para(
        "All shared state (log buffer, statistics, anomaly ring) is protected by a single "
        "mutex (audit_mutex). This ensures thread safety when multiple user-space processes "
        "concurrently access the device node. The anomaly_check_burst() function is called "
        "while the mutex is already held by audit_log_event(), avoiding deadlocks."
    )

    # ── 3. Design Step-by-Step ──
    d.h1("3. Design Step-by-Step: Building the Driver")
    d.para(
        "This section describes the systematic design process followed to construct the "
        "USB file transfer activity driver. Each step builds upon the previous one, "
        "enabling readers to understand and replicate the design."
    )

    d.h2("Step 1: Define the Shared Contract (usb_tracker.h)")
    d.para(
        "Before writing any kernel or user code, we defined the data structures and ioctl "
        "commands that both sides must agree upon. This header file serves as the contract "
        "between kernel-space and user-space. Key definitions include:"
    )
    d.bullet("usb_audit_log_entry_t — A single event record with timestamp, PID, event type, file path, and size.")
    d.bullet("usb_audit_stats_t — Aggregate counters for total bytes, file counts, device events, and alerts.")
    d.bullet("usb_audit_anomaly_t — Configuration and status for the anomaly detection engine.")
    d.bullet("ioctl command macros (USB_AUDIT_GET_STATS, USB_AUDIT_SET_ANOMALY, etc.) using the Linux _IO/_IOR/_IOW/_IOWR macros.")
    d.para(
        "The magic number 'U' (0x55) was chosen to uniquely identify our driver's ioctl "
        "commands, preventing collisions with other drivers in the system."
    )

    d.h2("Step 2: Create the Character Device Skeleton")
    d.para(
        "The kernel module begins with a character device skeleton: alloc_chrdev_region() "
        "dynamically allocates a major number, cdev_init() and cdev_add() register the "
        "device with the kernel, and class_create()/device_create() automatically create "
        "the /dev/usb_audit node. The file_operations table maps system calls (open, read, "
        "write, ioctl) to our handler functions."
    )

    d.h2("Step 3: Implement the Circular Log Buffer")
    d.para(
        "A fixed-size array of 128 usb_audit_log_entry_t structures serves as the event "
        "log. A head pointer tracks the next write position. When the buffer is full, the "
        "oldest entry is overwritten. This prevents unbounded memory growth — a critical "
        "requirement for kernel code. The log_count variable tracks how many valid entries "
        "are currently stored."
    )

    d.h2("Step 4: Add USB Hotplug Monitoring")
    d.para(
        "The usb_register_notify() API registers a callback that fires whenever any USB "
        "device is added or removed. Our filter checks bDeviceClass against "
        "USB_CLASS_MASS_STORAGE (0x08) to only track storage devices. Each insertion or "
        "removal is logged as a DEVICE_IN or DEVICE_OUT event."
    )

    d.h2("Step 5: Build the ioctl Command Dispatcher")
    d.para(
        "The unlocked_ioctl handler validates the magic number and command number, then "
        "dispatches to the appropriate handler. Each handler uses copy_to_user() and "
        "copy_from_user() to safely transfer data across the kernel/user boundary. "
        "Supported commands: GET_STATS, CLEAR_LOGS, SET_PATH, GET_LOGS, RESET_STATS, "
        "SET_ANOMALY, and GET_ANOMALY."
    )

    d.h2("Step 6: Implement the Anomaly Detection Engine")
    d.para(
        "A 64-entry ring buffer stores ktime_t timestamps of every FILE_CREATE and "
        "FILE_MODIFY event. After recording each timestamp, the engine counts how many "
        "entries fall within the configured sliding window (default: 3000 ms). If the "
        "count exceeds the threshold (default: 5) and the cooldown period (5000 ms) has "
        "elapsed, an ALERT event is automatically logged. The cooldown prevents alert "
        "flooding during sustained bursts."
    )

    d.h2("Step 7: Create the User-Space Application")
    d.para(
        "The C application opens /dev/usb_audit with O_RDWR and uses ioctl() to retrieve "
        "statistics and logs. It provides both an interactive test menu (for injecting "
        "events and querying state) and a daemon dashboard mode (for periodic monitoring). "
        "Signal handlers ensure clean shutdown on SIGINT/SIGTERM."
    )

    d.h2("Step 8: Automate with Bash and Makefile")
    d.para(
        "A top-level Makefile orchestrates kernel module compilation (via Kbuild) and "
        "user-space compilation (via gcc). The run.sh script automates the full lifecycle: "
        "build, insmod, device verification, application launch, and cleanup on exit."
    )

    # ── 4. Kernel Module ──
    d.h1("4. Kernel Module — Detailed Design")
    d.h2("4.1 Module Metadata & Initialisation")
    d.para(
        "The module declares its license (GPL), author, description, and version using "
        "the MODULE_* macros. The __init function (usb_audit_init) executes when the "
        "module is loaded via insmod. It performs six sequential steps with full error "
        "unwinding: (1) allocate device region, (2) register cdev, (3) create sysfs class "
        "and /dev node, (4) allocate log buffer, (5) initialise statistics and anomaly "
        "state, (6) register USB notifier."
    )
    d.para(
        "If any step fails, the function unwinds by reversing the initialisation order "
        "and returns a negative error code. This is critical kernel programming practice."
    )

    d.h2("4.2 File Operations")
    d.table(
        ["Operation", "Handler", "Description"],
        [
            ["open", "usb_audit_open", "Logs the access; always succeeds."],
            ["release", "usb_audit_release", "Logs the close; always succeeds."],
            ["read", "usb_audit_read", "Returns oldest log entry; 0 = no data."],
            ["write", "usb_audit_write", "Parses event code + path; logs event."],
            ["unlocked_ioctl", "usb_audit_ioctl", "Dispatches 7 ioctl commands."],
        ]
    )

    d.h2("4.3 USB Notifier Callback")
    d.para(
        "The usb_audit_notify() function is invoked by the USB core on device add/remove "
        "events. It casts the void pointer to struct usb_device, checks bDeviceClass for "
        "USB_CLASS_MASS_STORAGE, and logs the vendor ID, product ID, and serial number. "
        "For devices with bDeviceClass == 0x00 (per-interface class), it still proceeds "
        "since many USB storage devices report their class at the interface level."
    )

    d.h2("4.4 Circular Buffer Implementation")
    d.para(
        "The circular buffer uses modulo arithmetic for wrap-around: new entries are "
        "written at log_head, which advances as (log_head + 1) % USB_AUDIT_LOG_MAX. "
        "The oldest entry is at (log_head - log_count + LOG_MAX) % LOG_MAX. Reading "
        "removes the oldest entry (destructive read), decrementing log_count."
    )

    d.h2("4.5 Error Handling & Debugging")
    d.para(
        "Every function that can fail returns an appropriate errno value (-ENOMEM, "
        "-EFAULT, -EINVAL, -ENOTTY). printk() messages at KERN_INFO, KERN_WARNING, "
        "and KERN_ERR levels provide runtime visibility. The module initialisation "
        "function includes a full goto-based error unwind path, which is the standard "
        "Linux kernel pattern for resource cleanup."
    )

    # ── 5. User-Space App ──
    d.h1("5. User-Space Application — Detailed Design")
    d.h2("5.1 Program Structure")
    d.para(
        "usb_monitor.c is a single-file C program with modular helper functions. "
        "It uses only POSIX APIs (open, close, read, write, ioctl, signal) and "
        "standard C library functions, ensuring portability across Linux systems."
    )

    d.h2("5.2 Interactive Mode")
    d.para(
        "The interactive menu provides a command-line interface for testing and "
        "demonstration. Commands include: C/M/D for file events, A for manual alert, "
        "T for threshold configuration, S for statistics, L for logs, R for reset, "
        "X for clearing logs, and Q for quit. After each file event, the program "
        "automatically queries the kernel's anomaly status and displays any active alerts."
    )

    d.h2("5.3 Daemon Mode")
    d.para(
        "Daemon mode refreshes the terminal every 2 seconds, displaying a dashboard "
        "with aggregate statistics, anomaly status, and the 8 most recent log entries. "
        "This mode is suitable for long-running monitoring sessions."
    )

    d.h2("5.4 Signal Handling")
    d.para(
        "SIGINT and SIGTERM are caught to set a global flag (keep_running = 0), "
        "allowing clean exit from both interactive and daemon loops. The signal "
        "handler uses sig_atomic_t for safe flag access."
    )

    # ── 6. Python Watchdog ──
    d.h1("6. Python Watchdog Monitor")
    d.para(
        "file_tracker.py provides an alternative user-space monitoring approach using "
        "the watchdog library. It watches the USB mount point for real-time filesystem "
        "events without requiring the kernel module."
    )

    d.h2("6.1 Event Handlers")
    d.para(
        "The USBMonitorHandler class overrides on_created(), on_modified(), and "
        "on_closed() from FileSystemEventHandler. Both on_created() and on_modified() "
        "feed timestamps into the anomaly detection engine, ensuring comprehensive "
        "coverage of file write operations. The on_closed() handler reports the final "
        "file size after the write operation completes."
    )

    d.h2("6.2 Anomaly Detection (Python)")
    d.para(
        "The Python-side anomaly detection uses a sliding window identical in logic "
        "to the kernel-side engine. modification_history stores timestamps; on each "
        "event, entries older than TIME_WINDOW seconds are filtered out. If the "
        "remaining count exceeds ALERT_THRESHOLD, a [SECURITY ALERT] message is printed."
    )

    # ── 7. Anomaly Detection ──
    d.h1("7. Anomaly Detection Engine — Complete Design")
    d.h2("7.1 Kernel-Side Implementation")
    d.para(
        "The kernel-side anomaly engine is implemented in anomaly_check_burst() within "
        "usb_audit.c. Key design decisions:"
    )
    d.bullet("Ring buffer of 64 ktime_t values stores event timestamps chronologically.")
    d.bullet("Sliding window: ktime_sub_ns(now, window_ms * 1,000,000) computes the window start.")
    d.bullet("Burst counting: iterates backward from the most recent entry; breaks on first out-of-window entry (chronological optimisation).")
    d.bullet("Cooldown: a 5-second cooldown prevents repeated alerts during sustained bursts.")
    d.bullet("Alert recording: when triggered, an ALERT log entry is written directly into the circular buffer (mutex already held).")

    d.h2("7.2 Configuration Interface")
    d.para(
        "The anomaly engine is fully configurable at runtime via two ioctl commands: "
        "USB_AUDIT_SET_ANOMALY (sets threshold and window_ms) and USB_AUDIT_GET_ANOMALY "
        "(retrieves current config, burst_count, and alert_triggered flag). Both the C "
        "application (-t/-w flags, T command) and any custom user-space code can adjust "
        "these parameters without recompiling the kernel module."
    )

    d.h2("7.3 Multi-Layer Detection")
    d.para(
        "Anomaly detection operates at three independent layers: (1) kernel-side automatic "
        "detection in anomaly_check_burst(), (2) user-space polling via GET_ANOMALY ioctl "
        "in the C application, and (3) Python-side sliding window in file_tracker.py. "
        "This redundancy ensures alerts are raised even if one layer is not active."
    )

    # ── 8. Build System ──
    d.h1("8. Build System & Automation")
    d.h2("8.1 Makefile Architecture")
    d.para(
        "The top-level Makefile provides three targets: all (default, builds everything), "
        "kernel (delegates to src_kernel/Makefile via Kbuild), and user (compiles "
        "usb_monitor.c with gcc -Wall -Wextra -O2). The src_kernel/Makefile uses the "
        "kernel build system (obj-m := usb_audit.o) and locates headers automatically "
        "via /lib/modules/$(uname -r)/build."
    )

    d.h2("8.2 Bash Automation Script")
    d.para(
        "scripts/run.sh provides a one-command solution for the full lifecycle. "
        "It uses set -euo pipefail for strict error handling, colour-coded output "
        "for readability, and a trap on EXIT/INT/TERM to guarantee cleanup (rmmod, "
        "process termination). The script checks for root privileges, verifies kernel "
        "headers, builds both components, loads the module, verifies /dev/usb_audit, "
        "and launches the monitor."
    )

    # ── 9. ioctl API ──
    d.h1("9. Communication Protocol (ioctl API)")
    d.para(
        "All communication between user-space and kernel-space flows through ioctl "
        "system calls on the /dev/usb_audit file descriptor. The following table "
        "documents the complete API:"
    )

    d.table(
        ["Command", "Direction", "Data Type", "Description"],
        [
            ["GET_STATS (1)", "K→U", "usb_audit_stats_t", "Retrieve aggregate counters"],
            ["CLEAR_LOGS (2)", "–", "–", "Reset circular log buffer"],
            ["SET_PATH (3)", "U→K", "char[256]", "Set monitored mount path"],
            ["GET_LOGS (4)", "Bidirectional", "usb_audit_logs_t", "Batch-retrieve log entries"],
            ["RESET_STATS (5)", "–", "–", "Zero all counters + anomaly ring"],
            ["SET_ANOMALY (6)", "U→K", "usb_audit_anomaly_t", "Configure threshold & window"],
            ["GET_ANOMALY (7)", "K→U", "usb_audit_anomaly_t", "Query burst count & alert status"],
        ]
    )

    # ── 10. Testing ──
    d.h1("10. Testing & Verification")
    d.h2("10.1 Module Lifecycle")
    d.code("sudo insmod src_kernel/usb_audit.ko   # Load")
    d.code("lsmod | grep usb_audit                # Verify loaded")
    d.code("ls -la /dev/usb_audit                 # Verify device node")
    d.code("sudo rmmod usb_audit                  # Unload")
    d.code("dmesg | tail -20                      # Check kernel logs")

    d.h2("10.2 File Event Injection")
    d.para(
        "In the interactive monitor, inject file events to verify the logging pipeline:"
    )
    d.code("C /media/pi/USB/report.pdf    # Log a file CREATE")
    d.code("M /media/pi/USB/data.txt     # Log a file MODIFY")
    d.code("D /media/pi/USB/old.txt      # Log a file DELETE")
    d.code("S                            # Show updated statistics")

    d.h2("10.3 Mass-Copy Alert Test")
    d.para(
        "Rapidly inject 6 file create events to trigger the anomaly detector:"
    )
    d.code("C f1.txt    # t=0")
    d.code("C f2.txt    # t~0.5s")
    d.code("C f3.txt    # t~1.0s")
    d.code("C f4.txt    # t~1.5s")
    d.code("C f5.txt    # t~2.0s")
    d.code("C f6.txt    # ← ALERT! 6 ops in <3s > threshold of 5")
    d.para(
        "Verify via dmesg: dmesg | grep 'SECURITY ALERT' should show the kernel-side "
        "warning. The user app should display a prominent red alert banner."
    )

    d.h2("10.4 Demonstration Checklist")
    d.table(
        ["#", "Requirement", "Verification Method"],
        [
            ["1", "Module compilation", "make kernel exits 0"],
            ["2", "Module insertion", "insmod succeeds; /dev/usb_audit exists"],
            ["3", "Module removal", "rmmod succeeds; /dev/usb_audit removed"],
            ["4", "Hardware detection", "USB plug triggers DEVICE_IN in dmesg"],
            ["5", "App↔driver comm", "usb_monitor reads/writes/ioctls to /dev/usb_audit"],
            ["6", "dmesg logging", "dmesg | grep usb_audit shows events"],
            ["7", "User interaction", "Interactive menu commands processed"],
            ["8", "Clean shutdown", "run.sh trap calls rmmod on Ctrl+C"],
            ["9", "Mass-copy alert", "6 rapid C commands trigger auto-alert"],
        ]
    )

    # ── 11. Conclusion ──
    d.h1("11. Conclusion")
    d.para(
        "The USB File Transfer Activity Driver successfully meets all core and advanced "
        "project requirements. The kernel module (usb_audit.ko) implements a complete "
        "character device driver with USB hotplug monitoring, a circular event log buffer, "
        "seven ioctl commands, and an automatic mass-copy anomaly detection engine. The "
        "user-space C application (usb_monitor) provides an intuitive interface for "
        "monitoring, testing, and configuration."
    )
    d.para(
        "Key achievements include: (1) full kernel/user communication via a character "
        "device and ioctl protocol, (2) USB storage device hotplug detection using the "
        "kernel's notifier chain, (3) comprehensive printk() logging for dmesg auditing, "
        "(4) a configurable sliding-window anomaly detector that automatically raises "
        "security alerts, (5) a fully automated build-and-run pipeline via Makefile and "
        "Bash script, and (6) clean resource management with proper error unwinding."
    )
    d.para(
        "The system is ready for deployment on a Raspberry Pi 4 running Raspbian 64-bit "
        "and serves as a foundation for data loss prevention and cybersecurity auditing "
        "applications."
    )

    # ── Assemble final XML ──
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
            xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
            xmlns:o="urn:schemas-microsoft-com:office:office"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
            xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
            xmlns:v="urn:schemas-microsoft-com:vml"
            xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {d.build()}
  </w:body>
</w:document>"""

    return document_xml, make_styles_xml()


def main():
    doc_xml, styles_xml = build_document()

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with zipfile.ZipFile(OUTPUT_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", XML_CONTENT_TYPES)
        zf.writestr("_rels/.rels", XML_RELS)
        zf.writestr("word/_rels/document.xml.rels", XML_WORD_RELS)
        zf.writestr("word/document.xml", doc_xml.encode("utf-8"))
        zf.writestr("word/styles.xml", styles_xml.encode("utf-8"))

    size = os.path.getsize(OUTPUT_PATH)
    print(f"Report generated: {OUTPUT_PATH}")
    print(f"Size: {size:,} bytes")


if __name__ == "__main__":
    main()

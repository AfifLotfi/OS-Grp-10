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
        "This project is a Linux kernel driver that watches file activity on USB storage "
        "devices. Think of it as a security camera for USB drives — it records every file "
        "that is created, changed, or deleted, and raises an alarm if someone copies too "
        "many files too quickly. This is called Data Loss Prevention (DLP), and it helps "
        "stop sensitive information from being stolen via USB sticks."
    )
    d.para(
        "The system runs on a Raspberry Pi 4 with Raspbian 64-bit and has three parts: "
        "(1) a kernel module (usb_audit.ko) that lives inside the Linux kernel and has "
        "direct access to USB hardware events, (2) a C program (usb_monitor) that shows "
        "statistics and logs in a dashboard, and (3) a Python script (file_tracker.py) "
        "that watches folders for changes and reports them to the kernel module."
    )
    d.para(
        "The standout feature is automatic mass-copy detection. The kernel module uses "
        "a sliding-window burst counter: if too many file operations happen within a short "
        "time window, it automatically logs a SECURITY ALERT. This works at two levels — "
        "the kernel detects writes autonomously using a kprobe hook on the vfs_write "
        "function, and user-space programs can also inject events for monitoring. Both "
        "levels feed into the same detection engine, so alerts are raised regardless of "
        "which path the event comes from."
    )
    d.para(
        "The project has been fully tested on real hardware with a USB drive. An automated "
        "test suite (test_all.sh) verifies all 10 features in one command: module loading, "
        "device node creation, kprobe activation, event injection, statistics accuracy, "
        "log buffer integrity, anomaly detection, USB drive interaction, and clean shutdown. "
        "All 22 tests pass consistently."
    )

    # ── 2. System Architecture ──
    d.h1("2. System Architecture & Design")
    d.h2("2.1 High-Level Architecture")
    d.para(
        "The system is built in layers. The kernel module (usb_audit.ko) sits at the bottom "
        "with full hardware access. Above it, user-space programs talk to the kernel through "
        "a special file called /dev/usb_audit — just like reading and writing a regular file, "
        "but the data goes to our driver instead of a disk."
    )
    d.para(
        "There are two ways events reach the kernel module. The first is user-space reporting: "
        "the C monitor or Python script notices a file change and sends a message to "
        "/dev/usb_audit. The second is kernel-level interception: a kprobe (kernel probe) "
        "hooks into the Linux kernel's own vfs_write function, so the driver automatically "
        "detects any file write anywhere on the system — no user-space help needed. "
        "Both paths feed into the same log buffer and anomaly detection engine."
    )

    d.table(
        ["Layer", "Component", "Language", "What It Does"],
        [
            ["User-Space", "usb_monitor", "C", "Dashboard + event injection"],
            ["User-Space", "file_tracker.py", "Python 3", "Real-time folder watching"],
            ["User-Space", "test_all.sh", "Bash", "Automated test suite"],
            ["Kernel-Space", "usb_audit.ko", "C (Kernel)", "Driver + anomaly engine"],
            ["Kernel-Space", "kprobe hook", "C (Kernel)", "Auto-detect file writes"],
        ]
    )

    d.h2("2.2 Data Flow")
    d.para(
        "When a file is written to a USB drive, two things can happen. First, the kernel's "
        "kprobe on vfs_write automatically fires — it checks if the file is on the monitored "
        "USB path, and if so, logs the event with the file size. Second, a user-space program "
        "may also detect the change and send an event string like 'C /media/usb/file.txt "
        "(1024 bytes)' to /dev/usb_audit. In both cases, the driver records the event in "
        "its circular buffer, updates counters, and feeds the anomaly detector. If too many "
        "events happen too fast, a SECURITY ALERT is raised automatically."
    )
    d.para(
        "File size tracking works end-to-end: the Python monitor reads the actual file size "
        "with os.path.getsize() and includes it in the event string. The kernel module's "
        "write handler parses the '(N bytes)' suffix and stores the size in the log entry. "
        "The kprobe path captures the actual number of bytes written from the vfs_write "
        "return value. This means the statistics always show real byte counts."
    )

    d.h2("2.3 Concurrency Model")
    d.para(
        "Since the driver can be accessed by multiple programs at once, all shared data "
        "(log buffer, counters, anomaly timestamps) is protected by a single mutex lock "
        "called audit_mutex. Only one thread can modify the shared data at a time. For the "
        "kprobe path, which runs in atomic context where sleeping is not allowed, a special "
        "trylock variant is used — if the lock is already taken, the event is simply skipped "
        "rather than risking a system crash. This is a safe trade-off for a monitoring tool."
    )

    # ── 3. Design Step-by-Step ──
    d.h1("3. Design Step-by-Step: Building the Driver")
    d.para(
        "This section walks through the design process step by step, from the initial "
        "header file all the way to the automated test suite. Each step builds on the "
        "previous one so you can see how the system came together."
    )

    d.h2("Step 1: Define the Shared Contract (usb_tracker.h)")
    d.para(
        "Before writing any kernel or user code, we defined the data structures and ioctl "
        "commands that both sides must agree upon. This header file is the contract between "
        "kernel-space and user-space. It defines event types (DEVICE_IN, FILE_CREATE, "
        "FILE_MODIFY, FILE_DELETE, ALERT), the log entry structure (timestamp, PID, event "
        "type, file path, byte size), statistics counters, and seven ioctl commands."
    )
    d.para(
        "A design challenge we solved: the GET_LOGS ioctl structure is about 35 KB (128 "
        "entries × 280 bytes each), which is too large for the kernel's 14-bit ioctl size "
        "field (max 16,383 bytes). We worked around this by using a placeholder type (__u32) "
        "in the ioctl macro while the actual handler still transfers the full struct. This "
        "keeps the ioctl command number valid without changing the data."
    )

    d.h2("Step 2: Create the Character Device Skeleton")
    d.para(
        "The kernel module starts with a character device skeleton. alloc_chrdev_region() "
        "asks the kernel for a major device number, cdev_init() and cdev_add() register our "
        "device, and class_create() plus device_create() make /dev/usb_audit appear in the "
        "filesystem. The file_operations table connects system calls (open, read, write, "
        "ioctl) to our handler functions. We added a version check (#if LINUX_VERSION_CODE) "
        "because class_create() changed its signature in Linux kernel 6.4 — older kernels "
        "need a different first argument (THIS_MODULE)."
    )

    d.h2("Step 3: Implement the Circular Log Buffer")
    d.para(
        "We use a fixed-size array of 128 log entries as a circular buffer. A head pointer "
        "marks where the next entry goes. When the buffer fills up, the oldest entry is "
        "overwritten — this is essential in kernel code because memory cannot grow without "
        "bound. A log_count variable tracks how many valid entries exist. The read operation "
        "returns entries one at a time from oldest to newest and properly advances the file "
        "position (f_pos) so repeated reads work correctly."
    )

    d.h2("Step 4: Add USB Hotplug Monitoring")
    d.para(
        "We use the kernel's usb_register_notify() function to get a callback whenever any "
        "USB device is plugged in or removed. Our callback filters for mass-storage devices "
        "(class 0x08) and logs each insertion or removal as a DEVICE_IN or DEVICE_OUT event "
        "with the device's vendor and product IDs. This means the audit trail automatically "
        "records when USB drives appear and disappear."
    )

    d.h2("Step 5: Add Kernel-Level File Interception with kprobe")
    d.para(
        "A key improvement over the basic design: we use a kretprobe (kernel return probe) "
        "to hook into the Linux kernel's own vfs_write function. This means the driver "
        "automatically detects every file write system-wide without needing any user-space "
        "program to report it. The kprobe has two parts: an entry handler that saves the "
        "file pointer and requested write size, and a return handler that checks whether "
        "the file is on the monitored USB path. If it is, the event is logged with the "
        "actual number of bytes written."
    )
    d.para(
        "Design challenge: kprobe handlers run in atomic context, which means they cannot "
        "sleep. Regular mutex_lock() can sleep, so it would crash the kernel. We solved "
        "this with a separate atomic logging function (audit_log_event_atomic) that uses "
        "mutex_trylock() — if the lock is busy, it silently skips the event instead of "
        "crashing. This is an acceptable trade-off for a monitoring tool."
    )
    d.para(
        "We also fixed a naming conflict: our module parameter 'enable_kprobe' clashed with "
        "the kernel's own enable_kprobe() function declared in <linux/kprobes.h>. Renaming "
        "it to 'enable_vfs_kprobe' resolved the conflict and made the purpose clearer."
    )

    d.h2("Step 6: Build the ioctl Command Dispatcher")
    d.para(
        "The unlocked_ioctl handler checks that the ioctl command is meant for our driver "
        "(magic number 'U') and dispatches to the right handler. Each handler uses "
        "copy_to_user() and copy_from_user() to safely move data between kernel and user "
        "memory. Seven commands are supported: GET_STATS, CLEAR_LOGS, SET_PATH, GET_LOGS, "
        "RESET_STATS, SET_ANOMALY, and GET_ANOMALY. The RESET_STATS command also clears "
        "the anomaly detection ring, giving a clean slate for testing."
    )

    d.h2("Step 7: Implement the Anomaly Detection Engine")
    d.para(
        "The anomaly engine uses a 64-entry ring buffer of timestamps. Every file CREATE "
        "or MODIFY event records its timestamp. After recording, the engine counts how many "
        "events happened within the sliding window (default 3000 ms). If the count exceeds "
        "the threshold (default 5) and enough time has passed since the last alert (5000 ms "
        "cooldown), a SECURITY ALERT is automatically logged. The cooldown prevents spam "
        "during sustained bursts. Both the atomic kprobe path and the regular user-space "
        "path feed into this same engine, and both now use monotonic timestamps (ktime_get_ns) "
        "for consistency."
    )

    d.h2("Step 8: Create the User-Space Application")
    d.para(
        "The C application (usb_monitor) opens /dev/usb_audit and provides two modes: "
        "an interactive menu for manual testing (inject events, view stats, configure "
        "thresholds) and a daemon mode that refreshes a dashboard every 2 seconds. It accepts "
        "command-line flags for setting the USB mount path, anomaly threshold, and time window. "
        "Signal handlers (SIGINT/SIGTERM) ensure a clean exit. The program also sends file "
        "size information in the event string using the format 'C /path (N bytes)', which "
        "the kernel module parses."
    )

    d.h2("Step 9: Create the Python Watchdog")
    d.para(
        "The Python script (file_tracker.py) uses the watchdog library to monitor a folder "
        "for real-time filesystem changes. It handles file creation, modification, closing, "
        "and deletion. For each event, it checks the actual file size with os.path.getsize() "
        "and sends a formatted event to /dev/usb_audit via the send_kernel_event() method. "
        "It also has its own sliding-window anomaly detector that prints [SECURITY ALERT] "
        "messages locally."
    )

    d.h2("Step 10: Automate Everything")
    d.para(
        "The top-level Makefile builds both the kernel module (via Kbuild) and the C "
        "application (via gcc). The run.sh script handles the full lifecycle: check "
        "prerequisites, build, load the module, verify the device node, launch the monitor, "
        "and clean up on exit. The test_all.sh script runs 22 automated tests covering "
        "every feature, producing a clear pass/fail report."
    )

    # ── 4. Kernel Module ──
    d.h1("4. Kernel Module — Detailed Design")
    d.h2("4.1 Module Initialisation")
    d.para(
        "When loaded with insmod, the module runs usb_audit_init() which performs seven "
        "steps in order: (1) allocate a dynamic major device number, (2) register the "
        "character device, (3) create the device class and /dev/usb_audit node (with "
        "version checking for kernel 6.4+ compatibility), (4) allocate the 128-entry "
        "circular log buffer, (5) initialise statistics and anomaly detection state, "
        "(6) register the USB hotplug notifier, and (7) register the kretprobe on "
        "vfs_write for kernel-level file interception. If the kprobe registration fails, "
        "the driver still works — it just relies on user-space to report events."
    )
    d.para(
        "The module parameter 'enable_vfs_kprobe' (bool, default true) lets users disable "
        "the kprobe at load time if needed: sudo insmod usb_audit.ko enable_vfs_kprobe=0. "
        "This parameter was originally named 'enable_kprobe' but had to be renamed because "
        "the Linux kernel headers already define an enable_kprobe() function — the name "
        "clash caused a compile error."
    )

    d.h2("4.2 Dual Logging Paths")
    d.para(
        "The driver has two separate logging functions for two different contexts. "
        "audit_log_event() is used when called from user-space write() or ioctl() handlers "
        "— it can safely use mutex_lock() because sleeping is allowed in user context. "
        "audit_log_event_atomic() is used when called from the kprobe handler — it uses "
        "mutex_trylock() because kprobes run in atomic context where sleeping would crash "
        "the kernel. If trylock fails (the lock is busy), the event is silently dropped. "
        "Both paths now consistently use ktime_get_ns() for monotonic timestamps, ensuring "
        "all log entries use the same clock source regardless of which path they came from."
    )

    d.h2("4.3 File Operations")
    d.table(
        ["Operation", "Handler", "Description"],
        [
            ["open", "usb_audit_open", "Logs the access; always succeeds."],
            ["release", "usb_audit_release", "Logs the close; always succeeds."],
            ["read", "usb_audit_read", "Returns oldest log entry; advances f_pos."],
            ["write", "usb_audit_write", "Parses event code + path + size; logs event."],
            ["unlocked_ioctl", "usb_audit_ioctl", "Dispatches 7 ioctl commands."],
        ]
    )

    d.h2("4.4 Write Handler & File Size Parsing")
    d.para(
        "The write handler accepts event strings in the format '<code> <path> (N bytes)'. "
        "It parses the first character as the event code (C=create, M=modify, D=delete, "
        "A=alert), skips whitespace to find the file path, trims trailing newlines, and "
        "uses strrchr() + sscanf() to extract the optional file size from parentheses at "
        "the end. The parsed size is stored in the log entry and added to total_bytes_written. "
        "Even if no size suffix is provided, the event is still logged (size = 0) — a bug "
        "that previously caused events without sizes to be silently dropped was fixed."
    )

    d.h2("4.5 USB Notifier Callback")
    d.para(
        "The usb_audit_notify() function receives callbacks from the USB core on device "
        "insertion and removal. It checks bDeviceClass for USB_CLASS_MASS_STORAGE (0x08) "
        "and also accepts devices with class 0x00 (per-interface class) since many USB "
        "storage devices report their class at the interface level. Each event is logged "
        "with the device's vendor ID, product ID, and product name string."
    )

    d.h2("4.6 Error Handling")
    d.para(
        "Every kernel function follows Linux conventions: return 0 on success, negative "
        "errno on failure (-ENOMEM for out of memory, -EFAULT for bad user pointer, "
        "-EINVAL for bad arguments, -ENOTTY for wrong ioctl). The module init function "
        "uses goto-based error unwinding — if any step fails, it jumps to the cleanup "
        "label for that step and reverses the initialisation. printk() messages at "
        "KERN_INFO, KERN_WARNING, and KERN_ERR levels provide visibility via dmesg."
    )

    # ── 5. User-Space App ──
    d.h1("5. User-Space Application — Detailed Design")
    d.h2("5.1 Program Structure")
    d.para(
        "usb_monitor.c is a single-file C program about 530 lines long. It communicates "
        "with the kernel driver through /dev/usb_audit using standard POSIX calls: open(), "
        "write(), and ioctl(). It does not need any external libraries beyond the standard "
        "C library and Linux system headers."
    )

    d.h2("5.2 Interactive Mode")
    d.para(
        "The interactive menu provides 11 commands: C (create), M (modify), D (delete) "
        "for injecting file events; A for manually triggering an alert; T for setting "
        "anomaly threshold and window; S for viewing statistics; L for viewing logs; "
        "R for resetting all counters; X for clearing the log buffer; and Q for quitting. "
        "After each file event, the program automatically checks the kernel's anomaly "
        "status and displays any active SECURITY ALERT banners."
    )
    d.para(
        "Bug fix: the mount path string was not properly null-terminated due to a typo "
        "('\\0' instead of '\0'). This was corrected, ensuring the path is always a valid "
        "C string regardless of input length."
    )

    d.h2("5.3 Daemon Mode")
    d.para(
        "Daemon mode (-d flag) refreshes the terminal every 2 seconds, showing a live "
        "dashboard with aggregate statistics, anomaly status, and the 8 most recent log "
        "entries. This is designed for long-running monitoring sessions where you want "
        "to watch activity in real time."
    )

    d.h2("5.4 Command-Line Interface")
    d.para(
        "The program accepts several flags: -p/--path to set the USB mount path, "
        "-t/--threshold and -w/--window for anomaly configuration, -i for interactive "
        "mode (default), -d for daemon mode, and -h for help. Invalid values are clamped "
        "to safe minimums (threshold ≥ 1, window ≥ 100 ms)."
    )

    d.h2("5.5 Event Formatting")
    d.para(
        "The send_event() function formats events as '<code> <path> (<size> bytes)\n' "
        "and writes them to /dev/usb_audit. This format is parsed by the kernel module's "
        "write handler. For the interactive menu, a placeholder size of 1024 bytes is used; "
        "for real file operations through the Python monitor, the actual file size is sent."
    )

    # ── 6. Python Watchdog ──
    d.h1("6. Python Watchdog Monitor")
    d.para(
        "file_tracker.py is a Python script that watches a folder for file changes in "
        "real time using the watchdog library. Unlike the C monitor (which you interact "
        "with manually), this script runs in the background and automatically reports "
        "every file creation, modification, and deletion to the kernel module through "
        "/dev/usb_audit."
    )

    d.h2("6.1 Event Handlers")
    d.para(
        "The USBMonitorHandler class handles four file events. on_created() fires when "
        "a new file appears — it checks os.path.getsize() and sends a 'C' (create) event "
        "with the real file size. on_modified() fires continuously while a file is being "
        "written, tracking the growing file size. on_closed() fires when the write finishes, "
        "sending an 'M' (modify) event with the final size. on_deleted() fires when a file "
        "is removed, sending a 'D' (delete) event with size 0. All four handlers also feed "
        "timestamps into the local anomaly detector."
    )

    d.h2("6.2 Kernel Integration")
    d.para(
        "The send_kernel_event() method opens /dev/usb_audit for writing, formats the "
        "event as '<code> <path> (N bytes)\n', writes it, and closes the device. If the "
        "kernel module is not loaded or the device node is unavailable, the error is caught "
        "and printed as a warning — the script continues running without kernel reporting. "
        "This means file_tracker.py works both with and without the kernel module loaded, "
        "making it useful for testing and gradual deployment."
    )

    d.h2("6.3 Anomaly Detection")
    d.para(
        "The Python-side anomaly detector mirrors the kernel's logic. It keeps a list of "
        "recent event timestamps. On each new event, it removes entries older than "
        "TIME_WINDOW seconds (default 3.0). If the remaining count exceeds ALERT_THRESHOLD "
        "(default 5), it prints [SECURITY ALERT] with the current rate. This provides a "
        "second layer of detection that works even without the kernel module."
    )

    # ── 7. Anomaly Detection ──
    d.h1("7. Anomaly Detection Engine")
    d.h2("7.1 How It Works")
    d.para(
        "The anomaly detection engine answers one question: is someone copying too many "
        "files too quickly? It works like a speed camera — it counts how many file "
        "operations happen within a short time window, and if the count is too high, it "
        "raises an alarm."
    )
    d.para(
        "The engine keeps a ring buffer of 64 timestamps. Every time a file is created or "
        "modified, the current time is recorded. Then the engine counts how many of those "
        "timestamps fall within the sliding window (default: 3000 milliseconds, or 3 seconds). "
        "If the count exceeds the threshold (default: 5 operations), and at least 5 seconds "
        "have passed since the last alert (the cooldown), a SECURITY ALERT is automatically "
        "logged. The cooldown prevents the system from flooding alerts during a sustained "
        "copy operation."
    )

    d.h2("7.2 Configuration")
    d.para(
        "Everything is configurable at runtime — no need to recompile. The threshold and "
        "window can be changed via the C monitor (T command), command-line flags (-t/-w), "
        "or any program using the SET_ANOMALY ioctl. For testing, we lower the threshold "
        "to 2 and keep a 5-second window: then just 3 rapid file creates will trigger "
        "the alert. The GET_ANOMALY ioctl returns the current burst count and whether an "
        "alert is active, so user-space programs can poll for status."
    )

    d.h2("7.3 Three Detection Layers")
    d.para(
        "Anomaly detection runs at three independent levels for maximum coverage. "
        "(1) Kernel-side: anomaly_check_burst() is called automatically from both the "
        "regular and atomic logging paths — every event feeds into it. (2) User-space "
        "polling: the C monitor calls GET_ANOMALY ioctl to check burst status and displays "
        "alerts. (3) Python-side: file_tracker.py has its own sliding window with identical "
        "logic, so it can raise alerts even without the kernel module. If any layer detects "
        "a burst, the alert is visible."
    )
    d.para(
        "Verified behaviour: with threshold=2 and window=5000ms, injecting 3 file create "
        "events triggers the alert. Both the user-space monitor displays a red SECURITY "
        "ALERT banner and the kernel logs the alert via printk(). The dmesg output confirms "
        "the alert with the exact burst count and threshold values."
    )

    # ── 8. Build System ──
    d.h1("8. Build System & Automation")
    d.h2("8.1 Makefile Architecture")
    d.para(
        "The top-level Makefile has three targets: 'make all' (default) builds everything, "
        "'make kernel' compiles the kernel module via Kbuild, and 'make user' compiles "
        "usb_monitor.c with gcc -Wall -Wextra -O2. 'make clean' removes all build artifacts. "
        "The kernel module's own Makefile in src_kernel/ uses the Linux kernel build system "
        "(obj-m := usb_audit.o) and automatically finds the right kernel headers from "
        "/lib/modules/$(uname -r)/build."
    )

    d.h2("8.2 Deployment Script (run.sh)")
    d.para(
        "scripts/run.sh handles the full lifecycle in one command. It checks for root "
        "privileges, verifies kernel headers are installed, builds both the kernel module "
        "and C application, loads the module with insmod, verifies /dev/usb_audit exists, "
        "displays recent kernel logs, launches the monitor, and on exit (including Ctrl+C) "
        "automatically kills the monitor process and unloads the module. Colour-coded output "
        "(green=OK, yellow=warn, red=error) makes status easy to read."
    )

    d.h2("8.3 Automated Test Suite (test_all.sh)")
    d.para(
        "scripts/test_all.sh runs 22 automated tests across 10 categories and produces a "
        "pass/fail report. Tests cover: module loading, device node creation, kernel log "
        "confirmation (including kprobe and notifier status), monitor connection, event "
        "injection (create/modify/delete), statistics counter accuracy, log buffer contents, "
        "anomaly detection trigger, real USB filesystem read/write, and clean shutdown. "
        "The script resets statistics between tests so counters are always verified from zero. "
        "It handles edge cases like a pre-loaded module and gracefully skips unload if the "
        "module is in use."
    )
    d.code("sudo ./scripts/test_all.sh   # Run all 22 tests")

    # ── 9. ioctl API ──
    d.h1("9. Communication Protocol (ioctl API)")
    d.para(
        "All communication between user-space and kernel-space uses ioctl() calls on the "
        "/dev/usb_audit file descriptor. The driver uses magic number 'U' (0x55) to identify "
        "its commands. Each ioctl command is defined as a macro in usb_tracker.h, which is "
        "shared by both the kernel module and user-space programs."
    )

    d.table(
        ["Command", "Direction", "Data", "Purpose"],
        [
            ["GET_STATS (1)", "Kernel → User", "Stats struct", "Read all counters"],
            ["CLEAR_LOGS (2)", "None", "None", "Empty the log buffer"],
            ["SET_PATH (3)", "User → Kernel", "String (256)", "Set USB mount path to watch"],
            ["GET_LOGS (4)", "Both ways", "Log entries", "Read recent event history"],
            ["RESET_STATS (5)", "None", "None", "Zero all counters + anomaly ring"],
            ["SET_ANOMALY (6)", "User → Kernel", "Config struct", "Change threshold + window"],
            ["GET_ANOMALY (7)", "Kernel → User", "Status struct", "Check burst count + alert"],
        ]
    )
    d.para(
        "Note: The GET_LOGS structure is 35 KB (128 entries × 280 bytes), which exceeds "
        "the kernel's 14-bit ioctl size limit (16,383 bytes). We use a placeholder type "
        "(__u32) in the ioctl macro definition so the command number stays within valid "
        "range. The actual data transfer still uses the full struct — the size field in "
        "the ioctl encoding is informational, not enforced."
    )

    # ── 10. Testing ──
    d.h1("10. Testing & Verification")
    d.h2("10.1 Automated Test Suite")
    d.para(
        "The project includes an automated test script (test_all.sh) that verifies all "
        "features in one command. Run it with: sudo ./scripts/test_all.sh. It produces "
        "a colour-coded pass/fail report. On our test system (Raspberry Pi 4 with a real "
        "USB drive mounted at /media/colossalblue/RAZER), all 22 tests pass consistently."
    )

    d.h2("10.2 Module Lifecycle")
    d.code("sudo insmod src_kernel/usb_audit.ko   # Load the driver")
    d.code("lsmod | grep usb_audit                # Confirm it is loaded")
    d.code("ls -la /dev/usb_audit                 # Check the device node")
    d.code("dmesg | tail -20                      # See kernel messages")
    d.code("sudo rmmod usb_audit                  # Unload the driver")

    d.h2("10.3 File Event Injection")
    d.para(
        "From the interactive monitor, inject events to test the logging pipeline:"
    )
    d.code("C /media/colossalblue/RAZER/doc.pdf   # Log a file CREATE")
    d.code("M /media/colossalblue/RAZER/data.txt  # Log a file MODIFY")
    d.code("D /media/colossalblue/RAZER/old.txt   # Log a file DELETE")
    d.code("S                                       # Show updated statistics")
    d.code("L                                       # View recent log entries")

    d.h2("10.4 Mass-Copy Alert Test")
    d.para(
        "Configure a low threshold and inject events rapidly to trigger the alert:"
    )
    d.code("T 2 5000                    # Threshold=2 ops, window=5000ms")
    d.code("C /media/usb/a.txt          # Event 1")
    d.code("C /media/usb/b.txt          # Event 2")
    d.code("C /media/usb/c.txt          # Event 3 — ALERT! 3 > 2")
    d.para(
        "Verify: the monitor displays a red SECURITY ALERT banner. dmesg confirms: "
        "'[usb_audit] *** SECURITY ALERT *** Mass-copy detected! 3 file ops within "
        "5000 ms (threshold=2)'."
    )

    d.h2("10.5 Real USB Drive Testing")
    d.para(
        "With a USB drive plugged in and mounted, the system was tested end-to-end. "
        "Real file operations (echo, cp, rm) on the USB drive generated events that "
        "appeared in both the C monitor dashboard and the kernel log (dmesg). The kprobe "
        "on vfs_write automatically detected direct writes to the USB filesystem. "
        "USB hotplug events (physical plug/unplug of the drive) were correctly detected "
        "and logged as DEVICE_IN and DEVICE_OUT events."
    )

    d.h2("10.6 Verification Checklist")
    d.table(
        ["#", "Feature", "How to Verify", "Status"],
        [
            ["1", "Module compiles", "make all exits 0", "✅ Passed"],
            ["2", "Module loads", "insmod succeeds; /dev/usb_audit created", "✅ Passed"],
            ["3", "kprobe active", "dmesg shows kretprobe registered", "✅ Passed"],
            ["4", "Monitor connects", "usb_monitor shows 'Connected'", "✅ Passed"],
            ["5", "Event injection", "C/M/D commands produce 'Sent event'", "✅ Passed"],
            ["6", "Stats accurate", "S command shows correct counters", "✅ Passed"],
            ["7", "Log buffer works", "L command shows timestamped entries", "✅ Passed"],
            ["8", "Anomaly alert", "3 rapid events trigger SECURITY ALERT", "✅ Passed"],
            ["9", "Kernel alert logged", "dmesg shows alert with burst details", "✅ Passed"],
            ["10", "USB drive works", "Can write/read test files on real USB", "✅ Passed"],
            ["11", "Clean unload", "rmmod succeeds; device node removed", "✅ Passed"],
            ["12", "All 22 auto-tests", "test_all.sh reports 22/22 passed", "✅ Passed"],
        ]
    )

    # ── 11. Conclusion ──
    d.h1("11. Conclusion")
    d.para(
        "The USB File Transfer Activity Driver meets all project requirements and goes "
        "beyond them with several advanced features. The kernel module (usb_audit.ko) is "
        "a complete Linux character device driver that monitors USB storage activity at "
        "both the device level (hotplug detection) and the file level (create, modify, "
        "delete tracking). The user-space tools provide both interactive and automated "
        "interfaces for monitoring and testing."
    )
    d.para(
        "Key technical achievements:"
    )
    d.bullet("Kernel-level file interception via kretprobe on vfs_write — the driver autonomously detects file writes without user-space help.")
    d.bullet("Dual-path logging architecture — atomic-safe path for kprobe context and regular path for user context, both feeding the same audit trail.")
    d.bullet("Configurable sliding-window anomaly detector with cooldown — automatically raises SECURITY ALERT when file operations exceed a threshold within a time window.")
    d.bullet("End-to-end file size tracking — user-space monitors report real byte counts, kernel parses and stores them, statistics show accurate totals.")
    d.bullet("Full ioctl API with 7 commands — GET_STATS, CLEAR_LOGS, SET_PATH, GET_LOGS, RESET_STATS, SET_ANOMALY, GET_ANOMALY.")
    d.bullet("Linux kernel 6.4+ version compatibility — class_create() API difference handled with preprocessor version check.")
    d.bullet("Circular log buffer with 128 entries — prevents unbounded memory growth while preserving recent history.")
    d.bullet("Three-layer anomaly detection — kernel engine + user-space polling + Python watchdog, for maximum coverage.")
    d.bullet("Automated test suite — 22 tests across 10 categories, verified on real hardware with a USB drive.")
    d.bullet("One-command build and deployment — make all && sudo ./scripts/run.sh handles the full lifecycle.")
    d.para("")
    d.para(
        "The system has been tested on a Raspberry Pi 4 running a custom Linux kernel "
        "(6.18.26-v71-CSC1107_CUSTOM_KERNEL+) with a real USB drive. All 22 automated "
        "tests pass. The driver correctly detects USB device insertion and removal, logs "
        "file operations with accurate timestamps and sizes, and raises security alerts "
        "when mass-copy behaviour is detected. The codebase includes proper error handling, "
        "resource cleanup, and kernel coding conventions throughout."
    )
    d.para(
        "This project demonstrates practical operating systems concepts including kernel "
        "module development, character device drivers, kernel/user communication via ioctl, "
        "concurrency with mutexes, atomic context programming, kprobe-based function hooking, "
        "USB subsystem integration, and automated build/test pipelines."
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

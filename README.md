Markdown
# Group 10 - Project 15: USB File Transfer Activity Driver

This project implements a hybrid storage monitoring system on the Raspberry Pi 4 for data loss prevention and cybersecurity auditing. It tracks file transfers to removable USB storage devices using a kernel-space monitoring module and a user-space anomaly detection application.

## Directory Structure

```text
OS_Grp_10/
├── .gitignore          # Build exclusion configurations
├── README.md           # System documentation and execution steps
├── src_kernel/         # Linux Kernel Module source files
│   ├── Makefile        # Kbuild compilation script
│   └── usb_audit.c     # Driver source file tracking block requests
└── src_user/           # User-space monitoring application
    └── file_tracker.py # Python event monitor with mass-copy detection
Prerequisites
The system must be compiled and executed on a Raspberry Pi 4 running Linux.

1. Install Kernel Headers and Build Essentials
The custom kernel module requires development headers matching your current running kernel:

Bash
sudo apt update && sudo apt install raspberrypi-kernel-headers build-essential -y
2. Install User-Space Dependencies
The Python monitoring daemon requires the system-wide filesystem notification package:

Bash
sudo apt install python3-watchdog -y
Setup and Execution Steps
1. Identify the USB Mount Point
Plug in your target USB flash drive and verify its partition mounting path using the block storage utility:

Bash
lsblk
Locate the device node (typically /dev/sda1) and find its corresponding directory under the MOUNTPOINT column (e.g., /media/afifpi/Samsung USB). Ensure the USB_TARGET_PATH variable in src_user/file_tracker.py is configured to match this exact path.

2. Run the User-Space Daemon
Execute the audit script to begin real-time filesystem monitoring:

Bash
python3 src_user/file_tracker.py
3. Verify File Activity Tracking
Open a secondary terminal session and trigger a file write operation to test the monitoring output:

Bash
echo "System testing protocol" > "/media/afifpi/Samsung USB/test_log.txt"
The active daemon window will display output logs verifying file creation, modification flags, and total byte metrics.

4. Test Advanced Mass-Copy Anomaly Detection
The user-space engine evaluates the frequency of filesystem modifications over a sliding window. To simulate a malicious mass data extraction behavior and verify the alert threshold, run the following loop from a secondary terminal:

Bash
for i in {1..10}; do echo "data" > "/media/afifpi/Samsung USB/file_$i.txt"; sleep 0.1; done
The application terminal will log standard transactions for the first 5 operations and then trigger a targeted security warning message upon processing the 6th sequential block manipulation within the timeframe:

Plaintext
[SECURITY ALERT] Suspicious mass-copy behavior detected!
                 Rate: 6 file ops in < 3.0s
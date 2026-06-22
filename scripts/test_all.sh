#!/bin/bash
#
# test_all.sh — Automated Test Suite for USB File Transfer Activity Driver
#
# Tests every feature end-to-end and produces a pass/fail report.
# Run:   chmod +x scripts/test_all.sh && sudo ./scripts/test_all.sh
#

set -euo pipefail

USB_PATH="${1:-/media/colossalblue/RAZER}"
MODULE_PATH="./src_kernel/usb_audit.ko"
MONITOR_BIN="./src_user/usb_monitor"
DEVICE_NODE="/dev/usb_audit"
TMP_OUT="/tmp/usb_audit_test_output.txt"
PASS=0
FAIL=0
TOTAL=0

GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# ── Helpers ────────────────────────────────────────────────────────────

pass() { echo -e "  ${GREEN}[PASS]${NC} $1"; PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); }
fail() { echo -e "  ${RED}[FAIL]${NC} $1 — $2"; FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); }

banner() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
}

run_interactive() {
    # Send commands to the monitor and capture output
    printf "%s\n" "$@" | timeout 8 "$MONITOR_BIN" -p "$USB_PATH" 2>&1 || true
}

# ── Check root ─────────────────────────────────────────────────────────

if [[ $EUID -ne 0 ]]; then
    echo "Must run as root: sudo ./scripts/test_all.sh"
    exit 1
fi

banner "USB File Transfer Activity Driver — Automated Test Suite"
echo "Target USB path: $USB_PATH"
echo ""

# ── TEST 1: Module can be loaded ───────────────────────────────────────

banner "Test 1: Load Kernel Module"

if lsmod | grep -q "^usb_audit "; then
    echo "  Module already loaded, removing first..."
    rmmod usb_audit 2>/dev/null || true
    sleep 1
fi

if [[ -f "$MODULE_PATH" ]]; then
    if insmod "$MODULE_PATH" 2>&1; then
        pass "Module loaded successfully"
    else
        fail "Module load failed" "$(dmesg | tail -3)"
    fi
else
    fail "Module not found" "Run 'make all' first ($MODULE_PATH missing)"
fi

# ── TEST 2: Device node exists ─────────────────────────────────────────

banner "Test 2: Device Node"

if [[ -e "$DEVICE_NODE" ]]; then
    pass "Device node $DEVICE_NODE exists"
else
    fail "Device node missing" "$DEVICE_NODE not found — check dmesg"
fi

# ── TEST 3: Module shows in dmesg ──────────────────────────────────────

banner "Test 3: Kernel Log Confirmation"

if dmesg | grep -q "usb_audit.*Driver loaded successfully"; then
    pass "Kernel log confirms driver loaded"
else
    fail "No kernel confirmation" "dmesg missing load message"
fi

if dmesg | grep -q "kretprobe on vfs_write registered"; then
    pass "kprobe is ACTIVE (kernel-level interception enabled)"
else
    fail "kprobe not active" "kernel-level interception unavailable"
fi

if dmesg | grep -q "USB hotplug notifier registered"; then
    pass "USB hotplug notifier registered"
else
    fail "Hotplug notifier missing" "USB plug/unplug won't be detected"
fi

# ── TEST 4: Monitor connects ───────────────────────────────────────────

banner "Test 4: Monitor Connection"

MON_OUT=$(timeout 3 "$MONITOR_BIN" -p "$USB_PATH" 2>&1 <<< "Q" || true)

if echo "$MON_OUT" | grep -q "Connected to $DEVICE_NODE"; then
    pass "Monitor connected to $DEVICE_NODE"
else
    fail "Monitor connection failed" "$(echo "$MON_OUT" | head -3)"
fi

if echo "$MON_OUT" | grep -q "Monitor path set to: $USB_PATH"; then
    pass "Monitor path set correctly"
else
    fail "Monitor path wrong" "Expected: $USB_PATH"
fi

# ── TEST 5: Event injection (C/M/D) ────────────────────────────────────

banner "Test 5: Event Injection (Create/Modify/Delete)"

EVT_OUT=$(run_interactive \
    "C ${USB_PATH}/test_create.txt" \
    "M ${USB_PATH}/test_modify.txt" \
    "D ${USB_PATH}/test_delete.txt" \
    "S" \
    "Q")

if echo "$EVT_OUT" | grep -q "Sent event: C"; then
    pass "CREATE event accepted"
else
    fail "CREATE event failed" "Check /dev/usb_audit write path"
fi

if echo "$EVT_OUT" | grep -q "Sent event: M"; then
    pass "MODIFY event accepted"
else
    fail "MODIFY event failed" "Check /dev/usb_audit write path"
fi

if echo "$EVT_OUT" | grep -q "Sent event: D"; then
    pass "DELETE event accepted"
else
    fail "DELETE event failed" "Check /dev/usb_audit write path"
fi

# ── TEST 6: Statistics counters work ───────────────────────────────────

banner "Test 6: Statistics Counters"

if echo "$EVT_OUT" | grep -q "Files created.*: 1"; then
    pass "Files created counter = 1"
else
    fail "Create counter wrong" "Expected 1"
fi

if echo "$EVT_OUT" | grep -q "Files modified.*: 1"; then
    pass "Files modified counter = 1"
else
    fail "Modify counter wrong" "Expected 1"
fi

if echo "$EVT_OUT" | grep -q "Files deleted.*: 1"; then
    pass "Files deleted counter = 1"
else
    fail "Delete counter wrong" "Expected 1"
fi

# ── TEST 7: Log entries visible ────────────────────────────────────────

banner "Test 7: Log Buffer"

if echo "$EVT_OUT" | grep -q "FILE_CREATE"; then
    pass "Log contains FILE_CREATE entries"
else
    fail "No FILE_CREATE in logs" "Log buffer may be empty"
fi

if echo "$EVT_OUT" | grep -q "FILE_MODIFY"; then
    pass "Log contains FILE_MODIFY entries"
else
    fail "No FILE_MODIFY in logs" "Log buffer may be empty"
fi

if echo "$EVT_OUT" | grep -q "FILE_DELETE"; then
    pass "Log contains FILE_DELETE entries"
else
    fail "No FILE_DELETE in logs" "Log buffer may be empty"
fi

# ── TEST 8: Anomaly detection ──────────────────────────────────────────

banner "Test 8: Anomaly Detection (Mass-Copy Alert)"

ANO_OUT=$(run_interactive \
    "T 2 5000" \
    "C ${USB_PATH}/burst_1.txt" \
    "C ${USB_PATH}/burst_2.txt" \
    "C ${USB_PATH}/burst_3.txt" \
    "Q")

if echo "$ANO_OUT" | grep -q "SECURITY ALERT"; then
    pass "SECURITY ALERT triggered by burst of 3 (threshold 2)"
else
    fail "No security alert" "Anomaly detection may not be working"
fi

if dmesg | grep -q "SECURITY ALERT.*Mass-copy detected"; then
    pass "Kernel also logged the security alert"
else
    fail "Kernel didn't log alert" "Check printk output"
fi

# ── TEST 9: USB drive filesystem interaction ───────────────────────────

banner "Test 9: Real USB Filesystem Interaction"

if [[ -d "$USB_PATH" ]]; then
    pass "USB mount point $USB_PATH exists"

    TEST_FILE="${USB_PATH}/_test_audit_file.txt"
    echo "automated test $(date)" > "$TEST_FILE" 2>/dev/null && {
        pass "Can write test file to USB drive"
        rm -f "$TEST_FILE"
    } || {
        fail "Cannot write to USB" "Permission issue or read-only mount"
    }
else
    fail "USB path not found" "$USB_PATH does not exist — plug in a USB drive"
fi

# ── TEST 10: Clean shutdown ────────────────────────────────────────────

banner "Test 10: Clean Shutdown"

if rmmod usb_audit 2>&1; then
    pass "Module unloaded cleanly"
else
    fail "Module unload failed" "$(dmesg | tail -3)"
fi

if [[ ! -e "$DEVICE_NODE" ]]; then
    pass "Device node removed after unload"
else
    fail "Device node still present" "Should have been cleaned up"
fi

# ── SUMMARY ─────────────────────────────────────────────────────────────

banner "RESULTS: $PASS / $TOTAL tests passed"

if [[ $FAIL -eq 0 ]]; then
    echo -e "  ${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  ${GREEN}  ✅  ALL TESTS PASSED — System is fully operational${NC}"
    echo -e "  ${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
else
    echo -e "  ${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  ${RED}  ❌  $FAIL test(s) FAILED — see details above${NC}"
    echo -e "  ${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
fi

echo ""

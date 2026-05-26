# Makefile — Kernel Module Build for USB File Transfer Activity Driver
#
# This Makefile uses the kernel build system (Kbuild) to compile the
# usb_audit.ko kernel module.  It automatically locates the running
# kernel's headers via `uname -r`.
#
# Targets:
#   make          — build the kernel module (usb_audit.ko)
#   make clean    — remove build artifacts
#
# Project:  Group 10 — USB File Transfer Activity Driver (Project 15)
# Course:   CSC1107 — Operating Systems
# Target:   Raspberry Pi 4, Raspbian 64-bit

# Name of the kernel module (no .ko suffix).
obj-m := usb_audit.o

# Path to the currently running kernel's build directory.
KDIR := /lib/modules/$(shell uname -r)/build

# Working directory for the build.
PWD  := $(shell pwd)

# -------------------------------------------------------------------------
# Default target: build the module
# -------------------------------------------------------------------------
all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

# -------------------------------------------------------------------------
# Clean target: remove all generated files
# -------------------------------------------------------------------------
clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
	@rm -f *.o *.ko *.mod.c *.mod *.order *.symvers

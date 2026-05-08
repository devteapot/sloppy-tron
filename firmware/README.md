# Firmware

This folder is for microcontroller or servo-controller bridge code.

V0 should avoid direct Raspberry Pi GPIO PWM for servos. Prefer a dedicated
controller or microcontroller bridge with a separate servo power rail and shared
ground.

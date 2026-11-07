# LILYGO T-Dongle-S3 PC Stat

For the original T-Dongle-S3 (ESP32-S3, 16 MB flash, 80 x 160 ST7735 LCD).
Not validated for Plus, Dual, or other ESP32 boards.

Stop the Windows helper and close serial monitors before connecting in the browser.
Hold BOOT while inserting the dongle, then release BOOT.
Connect/flash using desktop Chrome or Edge. Flashing replaces the existing firmware;
back up anything you want to keep first.

The precompiled binary includes the bootloader, partition table, OTA initialization,
and app. Its flash address is **0x0**. Do not flash the app-only build at this address.

When flashing finishes, disconnect the browser's serial connection or close its tab,
then unplug/reinsert the dongle without BOOT. Empty gauges (`--`) are normal until
the Windows helper sends readings.

Download the project ZIP from https://github.com/ayhanyildiz/lilygo-pc-stat/archive/refs/heads/main.zip
and extract it. Install Python 3.10+ if needed, then open PowerShell in the extracted
folder and run `./Setup.ps1`, followed by `& './Start Monitor.ps1'`.
The helper must run on the Windows PC you want to monitor. NVIDIA's driver-provided
`nvidia-smi` supplies GPU readings; CPU and RAM still work without it.

Full instructions: https://github.com/ayhanyildiz/lilygo-pc-stat#readme

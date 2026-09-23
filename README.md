# POCO F4 (munch) 144Hz

A clean 144Hz display mod and native refresh rate unlock for the POCO F4 / Redmi K40S (`munch`).

The POCO F4 comes with a Samsung E4 AMOLED panel. While officially capped at 120Hz on stock software, the panel hardware is physically capable of running at 144Hz. Other available modules have known issues: washed-out gray blacks, screen flicker, scanlines, and a 142Hz frame pacing bottleneck instead of a true 144Hz.

This project fixes those issues directly at the DTBO hardware level and provides a native 144Hz toggle in your phone's stock Display Settings.

---

## Screenshots

<p align="center">
  <img src="assets/settings_144hz.jpg" width="31%" alt="144Hz in MIUI Settings" />
  &nbsp;
  <img src="assets/ufotest_144hz.jpeg" width="31%" alt="144Hz UFO Test" />
  &nbsp;
  <img src="assets/samplerate.jpeg" width="31%" alt="144Hz Input Event Invoke Rate" />
</p>

---

## What's Improved?

* **True AMOLED Black**: Black pixels now turn completely off (0 nits), fixing the dark-gray glow present in older mods.
* **No Scanlines or Jitter**: Re-tuned panel drive timings to eliminate horizontal scanlines and micro-flicker.
* **Solid 144Hz Input Event Invoke Rate**: Corrected vertical porch timings so touch polling and display refresh run at a true 144Hz input event invoke rate instead of dropping to 142Hz.
* **Zero Idle-Drop**: Selected refresh rates stay solidly locked even when the screen is idle, eliminating the annoying 2-second idle drop and mode-switching flicker.
* **Narrowed Brightness Gap**: Significantly reduced the large brightness jump present in older mods so switching between 120Hz and 144Hz is much smoother (see Known Issues below).
* **Safe Refresh Rate Cap**: Disabled the unstable 164Hz overclock mode to keep the display panel safe from unnecessary strain.
* **Native Display Settings**: The included module adds a native 144Hz toggle directly into your official Display Settings menu—no third-party switcher apps needed.

---

## Downloads

Download the latest zip from GitHub Releases or the [`out/`](out/) folder:

1. **All-in-One Module (Recommended)** (`ksu_munch_144hz_display_unlock.zip`):
   * Universal installer for **KernelSU**, **Magisk**, **APatch**, or **TWRP**.
   * Flashes the 144Hz DTBO directly to your hardware partition.
   * Automatically backs up your current DTBO before flashing.
   * Volume key menu to select your ROM (Auto Detect, MIUI/HyperOS, or AOSP).
   * In MIUI/HyperOS: enables 144Hz in Settings with idle-drop fix.
   * In AOSP: sets up 144Hz natively and keeps the system clean.
2. **Standalone DTBO Flashable ZIP** (`twrp_munch_144hz_display_unlock.zip`):
   * TWRP recovery installer that flashes the DTBO partition and sets up Settings integration if root is present.

---

## How to Install

### Option A: All-in-One Module (Easiest)
1. Open the **KernelSU**, **Magisk**, or **APatch** app on your phone.
2. Go to the **Modules** tab, tap **Install from storage**, and select `ksu_munch_144hz_display_unlock.zip`.  
   *(You can also flash this ZIP directly in TWRP Recovery).*
3. When prompted, use your Volume keys:
   * **Vol +**: Auto-detect your ROM.
   * **Vol -**: Choose manually between MIUI/HyperOS and AOSP.
   * *(If you do nothing, it will automatically detect your ROM after 8 seconds).*
4. Reboot your phone.
5. In MIUI: Go to **Settings -> Display -> Refresh rate**, and select **144 Hz**.

### Option B: Standalone TWRP Flash
1. Boot your POCO F4 into **TWRP Recovery**.
2. Go to **Install**, select `twrp_munch_144hz_display_unlock.zip`, and swipe to flash.
3. Reboot to system.

### Updating Your Custom Kernel?
If you update or flash a custom kernel that overwrites the DTBO partition:
* You **do not** need to reinstall this module.
* The module has an automatic background guard. On your first boot after the kernel update, it detects the change and automatically restores the 144Hz DTBO.
* You will get a notification asking you to reboot. Simply restart your phone once more to re-apply 144Hz!

---

## How to Uninstall

To remove the mod:
* In **KernelSU / Magisk / APatch**: Tap **Remove** on the module and reboot. The uninstaller automatically restores your backed-up DTBO, removes module files, and resets display settings back to 120Hz.

---

## Compatibility

* **ROM**: Confirmed working on MIUI 13 (Android 12), MIUI 14, HyperOS, and AOSP custom ROMs.
* **Root Managers**: KernelSU, Magisk, and APatch (or rootless via TWRP).

---

## Known Issues & Feedback

* **Brightness Curve**: While the brightness gap is significantly reduced, the curve is still not a 100% identical match to 120Hz across every slider step due to physical OLED pulse emission differences at higher refresh rates.
* If you have ideas or know how to dial this curve in even closer, feel free to open an issue or submit a pull request on GitHub!

---

## Credits & Thanks

* **Author & Maintenance**: [fatidaprilian](https://github.com/fatidaprilian)
* **GitHub Repository**: [munch-144hz](https://github.com/fatidaprilian/munch-144hz)
* **Hardware Base**: Xiaomi & Black Shark (for the original E4 144Hz DSI parameters)

---

## Disclaimer

While tested and verified on the POCO F4 hardware, flash at your own risk. Always keep a backup of your stock DTBO before flashing.

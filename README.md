# POCO F4 (munch) 144Hz Display Calibration

A clean, calibrated 144Hz DTBO and native display settings unlock for the POCO F4 / Redmi K40S (`munch`).

The POCO F4 features a Samsung E4 AMOLED display (driven by the `r66451` DDIC). While officially limited to 120Hz on stock MIUI, the panel hardware is physically capable of running at 144Hz. Earlier community mods ported raw timings from the Black Shark 4, but that came with noticeable issues: washed-out gray blacks, panel flicker, scanlines, over-saturated colors, and a 142Hz frame pacing bug.

This project fixes those issues directly at the DTBO hardware level and provides a native 144Hz option in the stock MIUI display settings.

---

## Screenshots

<p align="center">
  <img src="assets/settings_144hz.jpg" width="45%" alt="144Hz in MIUI Settings" />
  &nbsp;&nbsp;
  <img src="assets/ufotest_144hz.jpeg" width="45%" alt="144Hz UFO Test" />
</p>

---

## What's Fixed & Improved?

* **Pure 0-nit True Black**: Fixed the cathode voltage (`ELVSS`) back to `42 12 42 12`. Blacks are completely turned off (0 nits) like an AMOLED should be, rather than glowing dark gray.
* **No More Scanlines or Flicker**: Tuned the gate driver slew rate (`41 41`) so the display stays crisp and clean without visible horizontal lines or artifacts.
* **Solid 144.0Hz Refresh Rate**: Fixed the vertical front porch from the old 580 lines down to 535 lines (`0x217`). Touch and display testers now report a consistent 144.0Hz rate instead of dipping to 142Hz.
* **Safe Refresh Rate Cap**: The unstable 164Hz overclock mode (`timing@4`) has been harmonized to 144Hz. If any app or script requests 164Hz or 167Hz, it safely runs at 144Hz instead.
* **Balanced Brightness**: Aligned the DAC gamma reference (`VREG1 26` / `VREG2 26`) closer to stock 120Hz factory values. While it's not a 100% mathematically identical match across every single slider level due to OLED pulse emission differences, it is very close now—no more blinding jumps when switching between refresh rates.
* **Native MIUI Display Settings**: With the included KernelSU / Magisk module, 144Hz shows up directly inside `Settings -> Display -> Refresh rate`. You don't need any third-party refresh rate switcher apps anymore.

---

## Downloads

Grab the latest files from the [`out/`](out/) folder or GitHub Releases:

1. **All-in-One Module (Recommended)** (`ksu_munch_144hz_display_unlock.zip`):
   * Universal installer for **KernelSU**, **Magisk**, **APatch**, or **TWRP**.
   * Flashes the calibrated 144Hz DTBO directly to your hardware partition.
   * Prompts you with an interactive volume key menu (Auto Detect, MIUI/HyperOS, or AOSP) with an 8-second timeout.
   * In MIUI/HyperOS: enables 144Hz in the stock Settings app.
   * In AOSP: sets up 144Hz natively and keeps the system clean.
2. **Standalone DTBO Flashable ZIP** (`twrp_144Munch_v5_3_parity26.zip`):
   * Traditional TWRP-only installer that solely flashes the DTBO partition (ideal if you are unrooted or prefer managing DTBO manually).

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

### Option B: Standalone TWRP Flash (Rootless)
1. Boot your POCO F4 into **TWRP Recovery**.
2. Go to **Install**, select `twrp_144Munch_v5_3_parity26.zip`, and swipe to flash.
3. Reboot to system.

---

## Compatibility

* **ROM**: Confirmed working on MIUI 13 (Android 12), MIUI 14, HyperOS, and AOSP custom ROMs.
* **Root Managers**: KernelSU, Magisk, and APatch (or rootless via TWRP).

---

## Credits & Thanks

* **Calibration & Maintenance**: [fatidaprilian](https://github.com/fatidaprilian)
* **Hardware Base**: Xiaomi & Black Shark (for the original E4 144Hz DSI parameters)
* **POCO F4 Community**: For testing and feedback

---

## Disclaimer

This is a community modification. While extensively tested and safe on the POCO F4 hardware, flash at your own risk. Always keep a backup of your stock DTBO before flashing.

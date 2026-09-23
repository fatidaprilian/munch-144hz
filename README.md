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

1. **DTBO Flashable ZIP** (`twrp_144Munch_v5_3_parity26.zip`): The calibrated DTBO containing 144.0Hz timings, true black, and balanced brightness.
2. **Settings Unlock Module** (`ksu_munch_144hz_display_unlock.zip`): Systemless module for KernelSU, Magisk, or APatch that unlocks the 144Hz option in MIUI Settings.

---

## How to Install

### Step 1: Flash the Calibrated DTBO
1. Boot your POCO F4 into **TWRP Recovery**.
2. Go to **Install**, select `twrp_144Munch_v5_3_parity26.zip`, and swipe to confirm.
3. Reboot to system.

### Step 2: Unlock 144Hz in MIUI Settings (Optional but Recommended)
1. Open the **KernelSU** or **Magisk** app on your phone.
2. Navigate to the **Modules** tab.
3. Tap **Install from storage**, select `ksu_munch_144hz_display_unlock.zip`, and install it.  
   *(You can also flash this ZIP directly in TWRP if you prefer).*
4. Reboot your phone.
5. Go to **Settings -> Display -> Refresh rate**, and select **144 Hz**.

---

## Compatibility

* **ROM**: Tested and confirmed working on MIUI 13 (Android 12). Should also work on MIUI 14 and HyperOS.
* **Root Managers**: KernelSU, Magisk, and APatch.
* **AOSP ROMs**: AOSP uses its own DTBO base on some trees. An AOSP-specific build will be added in a future update.

---

## Credits & Thanks

* **Calibration & Maintenance**: [fatidaprilian](https://github.com/fatidaprilian)
* **Hardware Base**: Xiaomi & Black Shark (for the original E4 144Hz DSI parameters)
* **POCO F4 Community**: For testing and feedback

---

## Disclaimer

This is a community modification. While extensively tested and safe on the POCO F4 hardware, flash at your own risk. Always keep a backup of your stock DTBO before flashing.

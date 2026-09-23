# POCO F4 (munch) 144Hz

A clean 144Hz display mod and native refresh rate unlock for the POCO F4 / Redmi K40S (`munch`).

The POCO F4 comes with a Samsung E4 AMOLED panel. While officially set to 120Hz on stock software, the panel hardware is physically capable of running at 144Hz. Earlier community mods ported raw timings from the Black Shark 4, but that came with noticeable bugs: washed-out gray blacks, screen flicker, scanlines, and a 142Hz frame pacing bottleneck.

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
* **Balanced Brightness**: Realigned brightness levels with the factory 120Hz mode so switching refresh rates is smooth with no blinding jumps.
* **Safe Refresh Rate Cap**: Disabled the unstable 164Hz overclock mode to keep the display panel safe from unnecessary strain.
* **Native Display Settings**: The included module adds a native 144Hz toggle directly into your official Display Settings menu—no third-party switcher apps needed.

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

## Known Issues & Feedback

* **Brightness Curve**: While brightness levels between 120Hz and 144Hz are now very close, they are not 100% mathematically 1:1 across every single slider step due to physical OLED pulse emission differences at higher refresh rates.
* If you have ideas or know how to dial this curve in even closer, feel free to open an issue or submit a pull request on GitHub!

---

## Credits & Thanks

* **Author & Maintenance**: [fatidaprilian](https://github.com/fatidaprilian)
* **Hardware Base**: Xiaomi & Black Shark (for the original E4 144Hz DSI parameters)
* **POCO F4 Community**: For testing and feedback

---

## Disclaimer

This is a community modification. While extensively tested and safe on the POCO F4 hardware, flash at your own risk. Always keep a backup of your stock DTBO before flashing.

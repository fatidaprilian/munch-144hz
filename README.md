# POCO F4 (munch) 144Hz Display Mod

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A clean display mod to enable 144Hz on the POCO F4 / Redmi K40S (`munch`).

The POCO F4 uses a Samsung E4 AMOLED panel that can run at 144Hz. However, older 144Hz mods often had issues with pale/washed-out colors, grey blacks, scanlines, or refresh rate dropping to 60Hz when idle. This project fixes those issues and adds a 144Hz option directly into your phone's Display Settings.

---

## Screenshots

<p align="center">
  <img src="assets/settings_144hz.jpg" width="31%" alt="144Hz in Settings" />
  &nbsp;
  <img src="assets/ufotest_144hz.jpeg" width="31%" alt="144Hz UFO Test" />
  &nbsp;
  <img src="assets/samplerate.jpeg" width="31%" alt="144Hz Touch Rate" />
</p>

---

## Features

* **144Hz in Settings**: Adds a 144Hz option directly into official Display Settings.
* **Direct FDT Injection**: Injects 144Hz timing directly into the factory stock Munch DTB without DTC recompilation, keeping native 60Hz and 120Hz modes, touchscreen, and fingerprint phandles completely untouched.
* **Clean Uninstaller**: Automatically backs up factory stock DTBO on install and restores it when the module is removed in KernelSU or Magisk.
* **Idle Refresh Rate Lock**: Keeps selected refresh rate steady without dropping to 60Hz when idle.

---

## Downloads

Download the latest files from GitHub Releases or the [`out/`](out/) folder:

1. **All-in-One Module (Recommended)** (`ksu_munch_144hz_display_unlock.zip`):
   * Universal installer for **KernelSU**, **Magisk**, **APatch**, or **TWRP**.
   * Flashes the 144Hz DTBO and automatically backs up the stock DTBO.
   * Enables 144Hz in MIUI/HyperOS Settings and configures system props.
2. **Standalone DTBO Flashable ZIP** (`twrp_munch_144hz_display_unlock.zip`):
   * Recovery installer for TWRP/OrangeFox.
3. **Raw DTBO Image** (`dtbo.img`):
   * For flashing via Fastboot: `fastboot flash dtbo dtbo.img`.

---

## How to Install

### Option A: Via KernelSU / Magisk / APatch (Recommended)
1. Open your root manager app (**KernelSU**, **Magisk**, or **APatch**).
2. Go to the **Modules** tab, tap **Install from storage**, and select `ksu_munch_144hz_display_unlock.zip`.
3. Wait for the installation to finish.
4. Reboot your phone.
5. In MIUI/HyperOS: Go to **Settings -> Display -> Refresh rate**, and choose **144 Hz**.

### Option B: Via TWRP Recovery
1. Boot into **TWRP Recovery**.
2. Select **Install**, choose `twrp_munch_144hz_display_unlock.zip` (or `ksu_munch_144hz_display_unlock.zip`), and swipe to flash.
3. Reboot to system.

### Option C: Via Fastboot
```bash
fastboot flash dtbo dtbo.img
```

---

## How to Uninstall

* If installed as a module: tap **Remove** in KernelSU/Magisk and reboot. The uninstaller restores your original stock DTBO automatically.
* If flashed via recovery or fastboot: restore your stock DTBO backup to the dtbo partition.

---

## Compatibility

* **ROMs**: MIUI 13, MIUI 14, HyperOS, and AOSP custom ROMs.
* **Root**: KernelSU, Magisk, APatch, or rootless (via fastboot).

---

## Known Notes

* **Brightness Shift**: At 144Hz, the panel fires 20% more refresh pulses per second compared to 120Hz, making screen luminance naturally slightly higher. If you prefer the 120Hz luminance level, simply lower your phone's brightness slider slightly (about 3–5%). Adjusting KCAL Value/HSV sliders is not recommended as it shifts the AMOLED subpixel white balance.
* **Sleep-Wake & Ambient Display**: Direct FDT injection preserves stock display wake sequences and True Black bias dividers, avoiding color tint regressions when turning the screen on/off.

---

## Credits

* **Author**: [fatidaprilian](https://github.com/fatidaprilian)
* **GitHub Repository**: [munch-144hz](https://github.com/fatidaprilian/munch-144hz)
* **Hardware Base**: Xiaomi & Black Shark (original E4 DSI parameters)

---

## Disclaimer

While tested and verified on the POCO F4 hardware, flash at your own risk. Always keep a backup of your stock DTBO before flashing.

---

## License

This project is licensed under the **GNU General Public License v3.0** (GPL-3.0). See the [LICENSE](LICENSE) file for details.

#!/usr/bin/env python3
"""
POCO F4 (munch) 144Hz Display Mod Builder
Author: fatidaprilian
"""

import os
import struct
import zipfile
import subprocess
import re

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
orig_dtbo_path = os.path.join(_root, 'reference', 'unpacked_twrp_144munch', 'dtbo.img')
out_dir = os.path.join(_root, 'out')
os.makedirs(out_dir, exist_ok=True)

with open(orig_dtbo_path, 'rb') as f:
    data = bytearray(f.read())

dtb_start = data.find(b'\xd0\x0d\xfe\xed')
if dtb_start != 0x40:
    raise RuntimeError(f"Unexpected DTB start offset: 0x{dtb_start:x}")

print("[*] Building POCO F4 144Hz DTBO...")

# 1. Patch timing@3 (144Hz mode)
# transfer-time-us: 6000us
tt3_off = dtb_start + 0x47ec8
data[tt3_off:tt3_off+4] = struct.pack('>I', 0x1770)

# v-front-porch: 580
vfp3_off = 0x47e74
data[vfp3_off:vfp3_off+4] = struct.pack('>I', 0x244)

# 2. Patch timing@4 (Cap to 144Hz)
# panel-framerate: 164 -> 144
fr4_off = 0x48a1c
data[fr4_off:fr4_off+4] = struct.pack('>I', 0x90)

# v-back-porch: 613 -> 580
vbp4_off = 0x48a8c
data[vbp4_off:vbp4_off+4] = struct.pack('>I', 0x244)

# v-front-porch: 613 -> 580
vfp4_off = 0x48a9c
data[vfp4_off:vfp4_off+4] = struct.pack('>I', 0x244)

# panel-clockrate: 1252MHz -> 1100MHz
clk4_off = 0x48b0c
data[clk4_off:clk4_off+4] = struct.pack('>I', 0x4190ab00)

# 3. Hardware registers (144Hz Calibration)
# Gate Drive: 41 41
data = bytearray(data.replace(bytes.fromhex("02b01439010000000003d33939"), bytes.fromhex("02b01439010000000003d34141")))
data = bytearray(data.replace(bytes.fromhex("02b09939010000000003d33939"), bytes.fromhex("02b09939010000000003d34141")))

# VREG2: 26
data = bytearray(data.replace(bytes.fromhex("02b0af39000000000002d318"), bytes.fromhex("02b0af39000000000002d326")))
data = bytearray(data.replace(bytes.fromhex("02b0b339000000000002d318"), bytes.fromhex("02b0b339000000000002d326")))

# ELVSS: 42 12 42 12
data = bytearray(data.replace(bytes.fromhex("02b05f39010000000005d3480e480e"), bytes.fromhex("02b05f39010000000005d342124212")))

# VREG1: 26
data = bytearray(data.replace(bytes.fromhex("02b02a39000000000002d32c"), bytes.fromhex("02b02a39000000000002d326")))
data = bytearray(data.replace(bytes.fromhex("02b02e39000000000002d32c"), bytes.fromhex("02b02e39000000000002d326")))

# Source bias: 04 47
# H-porch: d1 10


out_dtbo = os.path.join(out_dir, 'dtbo.img')
with open(out_dtbo, 'wb') as f:
    f.write(data)
print(f"[+] Output: {out_dtbo} ({os.path.getsize(out_dtbo)} bytes)")

# 4. Prepare Patched munch.xml
source_xml = os.path.join(_root, 'munch.xml')
with open(source_xml, 'r', encoding='utf-8') as f:
    xml_content = f.read()

old_fps_list = """    <integer-array name="fpsList">
        <item>120</item>
        <item>60</item>
    </integer-array>"""
new_fps_list = """    <integer-array name="fpsList">
        <item>144</item>
        <item>120</item>
        <item>60</item>
    </integer-array>"""

patched_xml = xml_content.replace(
    '<integer name="smart_fps_value">120</integer>',
    '<integer name="smart_fps_value">144</integer>'
).replace(old_fps_list, new_fps_list).replace(
    '<bool name="support_dc_backlight">false</bool>',
    '<bool name="support_dc_backlight">true</bool>'
).replace(
    '<integer name="defaultFps">60</integer>',
    '<integer name="defaultFps">144</integer>'
)

# 5. Shared Package Scripts
module_prop = """id=munch_144hz_display_unlock
name=POCO F4 144Hz Display Mod
version=release-hotfix
versionCode=145
author=fatidaprilian
description=Enables 144Hz DTBO and Settings toggle for POCO F4 (munch).
"""

system_prop = """# POCO F4 (munch) 144Hz Display Settings
ro.vendor.dfps.enable=false
ro.vendor.smart_dfps.enable=false
"""

service_sh = """#!/system/bin/sh
MODDIR=${0%/*}

until [ "$(getprop sys.boot_completed)" = "1" ]; do
  sleep 2
done
sleep 5

# Restore DTBO if overwritten by a kernel update
if [ -f "$MODDIR/dtbo.img" ]; then
  DTBO_BLK=""
  for part in "dtbo_a" "dtbo_b" "dtbo"; do
    for path in "/dev/block/bootdevice/by-name/$part" "/dev/block/by-name/$part" "/dev/block/mapper/$part"; do
      if [ -b "$path" ] || [ -e "$path" ]; then
        DTBO_BLK="$path"
        break 2
      fi
    done
  done

  if [ -n "$DTBO_BLK" ]; then
    DTBO_SIZE=$(wc -c < "$MODDIR/dtbo.img")
    CHECK_TMP="/data/local/tmp/dtbo_check"
    dd if="$DTBO_BLK" of="$CHECK_TMP" bs=4096 count=$(( (DTBO_SIZE + 4095) / 4096 )) 2>/dev/null

    if [ -f "$CHECK_TMP" ]; then
      if ! cmp -s -n "$DTBO_SIZE" "$MODDIR/dtbo.img" "$CHECK_TMP"; then
        for part in "dtbo_a" "dtbo_b" "dtbo"; do
          for path in "/dev/block/bootdevice/by-name/$part" "/dev/block/by-name/$part" "/dev/block/mapper/$part"; do
            if [ -b "$path" ] || [ -e "$path" ]; then
              dd if="$MODDIR/dtbo.img" of="$path" bs=4096 2>/dev/null
              break
            fi
          done
        done
        cmd notification post -S bigtext -t "POCO F4 144Hz" "Tag144" "Kernel update detected. 144Hz DTBO restored. Please reboot." 2>/dev/null
      fi
      rm -f "$CHECK_TMP"
    fi
  fi
fi

# Refresh rate lock daemon (prevents idle drop)
(
  LAST_FPS=""
  while true; do
    CURR_FPS=$(settings get system user_refresh_rate 2>/dev/null)
    if [ "$CURR_FPS" != "$LAST_FPS" ]; then
      case "$CURR_FPS" in
        144)
          settings put system min_refresh_rate 144.0 2>/dev/null
          settings put system peak_refresh_rate 144.0 2>/dev/null
          ;;
        120)
          settings put system min_refresh_rate 120.0 2>/dev/null
          settings put system peak_refresh_rate 120.0 2>/dev/null
          ;;
        60)
          settings put system min_refresh_rate 60.0 2>/dev/null
          settings put system peak_refresh_rate 60.0 2>/dev/null
          ;;
      esac
      LAST_FPS="$CURR_FPS"
    fi
    sleep 4
  done
) &
"""

uninstall_sh = """#!/system/bin/sh
if [ -f /data/adb/munch_stock_dtbo.img ]; then
  for part in "dtbo_a" "dtbo_b" "dtbo"; do
    for path in "/dev/block/bootdevice/by-name/$part" "/dev/block/by-name/$part" "/dev/block/mapper/$part"; do
      if [ -b "$path" ] || [ -e "$path" ]; then
        dd if=/data/adb/munch_stock_dtbo.img of="$path" bs=4096 2>/dev/null
        break
      fi
    done
  done
  rm -f /data/adb/munch_stock_dtbo.img
fi

settings delete system min_refresh_rate 2>/dev/null
settings put system peak_refresh_rate 120.0 2>/dev/null
settings put system user_refresh_rate 120 2>/dev/null
"""

# KSU / Magisk Installer
customize_sh = """#!/sbin/sh
choose_key() {
  local timeout=${1:-8}
  local start now key
  start=$(date +%s)
  while true; do
    key=$(timeout 0.2 getevent -qlc 1 2>/dev/null)
    case "$key" in
      *"KEY_VOLUMEUP"*"DOWN"*|*"KEY_VOLUMEUP"*" 1"*|*"KEY_VOLUMEUP"*"down"*)
        echo "UP"
        return 0
        ;;
      *"KEY_VOLUMEDOWN"*"DOWN"*|*"KEY_VOLUMEDOWN"*" 1"*|*"KEY_VOLUMEDOWN"*"down"*)
        echo "DOWN"
        return 0
        ;;
    esac
    now=$(date +%s)
    if [ $((now - start)) -ge $timeout ]; then
      echo "TIMEOUT"
      return 0
    fi
  done
}

ui_print "--------------------------------------------------"
ui_print "  POCO F4 (munch) 144Hz Display Mod               "
ui_print "  Author: fatidaprilian                           "
ui_print "  GitHub: https://github.com/fatidaprilian/munch-144hz "
ui_print "--------------------------------------------------"

ui_print " "
ui_print "--> Select Installation Mode:"
ui_print "  (Vol +) Auto Detect ROM"
ui_print "  (Vol -) Manual Selection"

CHOICE=$(choose_key 8)

if [ "$CHOICE" = "DOWN" ]; then
  ui_print " "
  ui_print "--> Select your ROM type:"
  ui_print "  (Vol +) MIUI / HyperOS"
  ui_print "  (Vol -) AOSP / Custom ROM"
  
  ROM_CHOICE=$(choose_key 10)
  if [ "$ROM_CHOICE" = "DOWN" ]; then
    ui_print "  Selected: AOSP / Custom ROM"
    TARGET_ROM="aosp"
  else
    ui_print "  Selected: MIUI / HyperOS"
    TARGET_ROM="miui"
  fi
else
  ui_print "  Selected: Auto Detect"
  IS_MIUI=0
  for prop in "ro.miui.ui.version.name" "ro.miui.ui.version.code" "ro.build.version.incremental"; do
    val=$(getprop "$prop" 2>/dev/null)
    if [ -n "$val" ]; then
      case "$val" in
        *V12*|*V13*|*V14*|*OS1*|*MIUI*|*HyperOS*) IS_MIUI=1; break ;;
      esac
    fi
  done
  if [ "$IS_MIUI" -eq 0 ] && [ -f "/system/build.prop" ]; then
    grep -qi "miui" /system/build.prop 2>/dev/null && IS_MIUI=1
  fi
  if [ -f "/product/etc/device_features/munch.xml" ] || [ -f "/vendor/etc/device_features/munch.xml" ]; then
    IS_MIUI=1
  fi

  if [ "$IS_MIUI" -eq 1 ]; then
    ui_print "  --> Detected: MIUI / HyperOS"
    TARGET_ROM="miui"
  else
    ui_print "  --> Detected: AOSP / Custom ROM"
    TARGET_ROM="aosp"
  fi
fi

ui_print " "
DTBO_BLK=""
for part in "dtbo_a" "dtbo_b" "dtbo"; do
  for path in "/dev/block/bootdevice/by-name/$part" "/dev/block/by-name/$part" "/dev/block/mapper/$part"; do
    if [ -b "$path" ] || [ -e "$path" ]; then
      DTBO_BLK="$path"
      break 2
    fi
  done
done

if [ -n "$DTBO_BLK" ] && [ ! -f /data/adb/munch_stock_dtbo.img ]; then
  ui_print "--> Backing up stock DTBO..."
  dd if="$DTBO_BLK" of="/data/adb/munch_stock_dtbo.img" bs=4096 2>/dev/null
fi

ui_print "--> Flashing 144Hz DTBO..."
FLASHED=0
for part in "dtbo_a" "dtbo_b" "dtbo"; do
  for path in "/dev/block/bootdevice/by-name/$part" "/dev/block/by-name/$part" "/dev/block/mapper/$part"; do
    if [ -b "$path" ] || [ -e "$path" ]; then
      dd if="$MODPATH/dtbo.img" of="$path" bs=4096 2>/dev/null && FLASHED=1
      break
    fi
  done
done

if [ "$FLASHED" -eq 1 ]; then
  ui_print "  [+] DTBO flashed successfully."
fi

ui_print " "
if [ "$TARGET_ROM" = "miui" ]; then
  ui_print "--> Configuring MIUI/HyperOS..."
  ui_print "  [+] 144Hz enabled in Settings"
  ui_print "  [+] DC Dimming enabled"
  ui_print "  [+] Idle-drop fix enabled"
else
  ui_print "--> Configuring AOSP..."
  ui_print "  [+] 144Hz active"
  rm -rf "$MODPATH/system"
fi

chmod 0755 "$MODPATH/service.sh" 2>/dev/null
chmod 0755 "$MODPATH/uninstall.sh" 2>/dev/null

ui_print " "
ui_print "--------------------------------------------------"
ui_print "  Installation completed. Please reboot.          "
ui_print "--------------------------------------------------"
"""

# 6. Package KSU / Magisk ZIP
ksu_zip = os.path.join(out_dir, 'ksu_munch_144hz_display_unlock.zip')
with zipfile.ZipFile(ksu_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    z.write(out_dtbo, 'dtbo.img')
    z.writestr('module.prop', module_prop)
    z.writestr('system.prop', system_prop)
    z.writestr('service.sh', service_sh)
    z.writestr('uninstall.sh', uninstall_sh)
    z.writestr('customize.sh', customize_sh)
    z.writestr('system/product/etc/device_features/munch.xml', patched_xml)
    z.writestr('system/product/etc/device_features/munch_global.xml', patched_xml)
    z.writestr('system/product/etc/device_features/munch_in.xml', patched_xml)
print(f"[+] Output: {ksu_zip} ({os.path.getsize(ksu_zip)} bytes)")

# 7. Package TWRP ZIP
twrp_install_sh = """#!/sbin/sh
umask 022
OUTFD=$2
ZIPFILE=$3

ui_print() {
  if [ -n "$OUTFD" ] && [ -e "/proc/self/fd/$OUTFD" ]; then
    echo "ui_print $1" > "/proc/self/fd/$OUTFD"
    echo "ui_print" > "/proc/self/fd/$OUTFD"
  else
    echo "$1"
  fi
}

ui_print "--------------------------------------------------"
ui_print "  POCO F4 (munch) 144Hz Display Mod               "
ui_print "  Author: fatidaprilian                           "
ui_print "  GitHub: https://github.com/fatidaprilian/munch-144hz "
ui_print "--------------------------------------------------"

mount /data 2>/dev/null

DTBO_BLK=""
for part in "dtbo_a" "dtbo_b" "dtbo"; do
  for path in "/dev/block/bootdevice/by-name/$part" "/dev/block/by-name/$part" "/dev/block/mapper/$part"; do
    if [ -b "$path" ] || [ -e "$path" ]; then
      DTBO_BLK="$path"
      break 2
    fi
  done
done

if [ -n "$DTBO_BLK" ] && [ ! -f /data/adb/munch_stock_dtbo.img ]; then
  ui_print "[*] Backing up stock DTBO..."
  mkdir -p /data/adb 2>/dev/null
  dd if="$DTBO_BLK" of="/data/adb/munch_stock_dtbo.img" bs=4096 2>/dev/null
fi

ui_print "[*] Flashing 144Hz DTBO..."
FLASHED=0
for part in "dtbo_a" "dtbo_b" "dtbo"; do
  for path in "/dev/block/bootdevice/by-name/$part" "/dev/block/by-name/$part" "/dev/block/mapper/$part"; do
    if [ -b "$path" ] || [ -e "$path" ]; then
      unzip -p "$ZIPFILE" dtbo.img > "$path" 2>/dev/null && FLASHED=1
      break
    fi
  done
done

if [ "$FLASHED" -eq 1 ]; then
  ui_print "  [+] DTBO flashed successfully."
fi

ui_print "[*] Configuring Settings Integration..."
if [ -d /data/adb/modules ] || [ -d /data/adb/ksu ] || [ -d /data/adb/magisk ] || [ -d /data/adb/ap ]; then
  MODPATH="/data/adb/modules/munch_144hz_display_unlock"
  mkdir -p "$MODPATH"
  unzip -o "$ZIPFILE" -x 'META-INF/*' -d "$MODPATH" >/dev/null 2>&1
  chmod -R 0755 "$MODPATH"
  find "$MODPATH" -type f -exec chmod 0644 {} + 2>/dev/null
  chmod 0755 "$MODPATH/service.sh" 2>/dev/null
  chmod 0755 "$MODPATH/uninstall.sh" 2>/dev/null
  ui_print "  [+] 144Hz option added to Settings"
  ui_print "  [+] Idle-drop fix enabled"
fi

ui_print " "
ui_print "--------------------------------------------------"
ui_print "  Installation completed. Please reboot.          "
ui_print "--------------------------------------------------"
exit 0
"""

twrp_zip = os.path.join(out_dir, 'twrp_munch_144hz_display_unlock.zip')
with zipfile.ZipFile(twrp_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    z.write(out_dtbo, 'dtbo.img')
    z.writestr('module.prop', module_prop)
    z.writestr('system.prop', system_prop)
    z.writestr('service.sh', service_sh)
    z.writestr('uninstall.sh', uninstall_sh)
    z.writestr('system/product/etc/device_features/munch.xml', patched_xml)
    z.writestr('system/product/etc/device_features/munch_global.xml', patched_xml)
    z.writestr('system/product/etc/device_features/munch_in.xml', patched_xml)
    z.writestr('META-INF/com/google/android/update-binary', twrp_install_sh)
    z.writestr('META-INF/com/google/android/updater-script', '#TWRP\n')

print(f"[+] Output: {twrp_zip} ({os.path.getsize(twrp_zip)} bytes)")
print("[+] All deliverables built successfully.")

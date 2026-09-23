import os, zipfile, shutil

# Paths
source_xml = '/home/ryuen/Project/munch-144hz/munch.xml'
out_dir = '/home/ryuen/Project/munch-144hz/out'
out_zip = os.path.join(out_dir, 'ksu_munch_144hz_display_unlock.zip')
dtbo_img = os.path.join(out_dir, 'dtbo.img')

if not os.path.exists(dtbo_img):
    raise RuntimeError(f"dtbo.img not found at {dtbo_img}. Please build DTBO first.")

with open(source_xml, 'r', encoding='utf-8') as f:
    xml_content = f.read()

# Verify targets exist
if '<integer name="smart_fps_value">120</integer>' not in xml_content:
    raise RuntimeError("Target smart_fps_value 120 not found in munch.xml")

old_fps_list = """    <integer-array name="fpsList">
        <item>120</item>
        <item>60</item>
    </integer-array>"""

if old_fps_list not in xml_content:
    raise RuntimeError("Target fpsList not found in munch.xml")

if '<bool name="support_smart_fps">true</bool>' not in xml_content:
    raise RuntimeError("Target support_smart_fps true not found in munch.xml")

# Patch values for MIUI/HyperOS (Disable Smart DFPS to prevent idle drop downclocking)
new_fps_list = """    <integer-array name="fpsList">
        <item>144</item>
        <item>120</item>
        <item>60</item>
    </integer-array>"""

patched_xml = xml_content.replace(
    '<integer name="smart_fps_value">120</integer>',
    '<integer name="smart_fps_value">144</integer>'
).replace(
    '<bool name="support_smart_fps">true</bool>',
    '<bool name="support_smart_fps">false</bool>'
).replace(old_fps_list, new_fps_list)

print("[*] Successfully prepared patched munch.xml for MIUI/HyperOS (support_smart_fps=false)")

# module.prop
module_prop = """id=munch_144hz_display_unlock
name=POCO F4 144Hz Display Mod
version=v5.3
versionCode=530
author=fatidaprilian
description=Flashes 144Hz DTBO and unlocks 144Hz in Settings. Auto-guards against kernel updates.
"""

# system.prop (Disables Xiaomi Dynamic FPS at vendor HAL level)
system_prop = """# POCO F4 (munch) 144Hz Display Settings
# Author: fatidaprilian
ro.vendor.dfps.enable=false
ro.vendor.smart_dfps.enable=false
"""

# customize.sh (Executed by KernelSU, Magisk, APatch, and TWRP direct installer)
customize_sh = """#!/sbin/sh
##########################################################################################
# POCO F4 (munch) 144Hz Display Mod Customization Script
# Author: fatidaprilian
##########################################################################################

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
ui_print "  ! Timeout in 8s defaults to Auto Detect"

CHOICE=$(choose_key 8)
TARGET_ROM=""

if [ "$CHOICE" = "DOWN" ]; then
  ui_print "  Selected: Manual Selection"
  ui_print " "
  ui_print "--> Select Your ROM Type:"
  ui_print "  (Vol +) MIUI / HyperOS"
  ui_print "  (Vol -) AOSP / Custom ROM"
  
  ROM_CHOICE=$(choose_key 15)
  if [ "$ROM_CHOICE" = "DOWN" ]; then
    ui_print "  Selected: AOSP / Custom ROM"
    TARGET_ROM="aosp"
  else
    ui_print "  Selected: MIUI / HyperOS"
    TARGET_ROM="miui"
  fi
else
  if [ "$CHOICE" = "TIMEOUT" ]; then
    ui_print "  ! Timeout reached, defaulting to Auto Detect..."
  else
    ui_print "  Selected: Auto Detect"
  fi
  
  # Auto detection logic
  IS_MIUI=0
  for prop in "ro.miui.ui.version.name" "ro.miui.ui.version.code" "ro.build.version.incremental"; do
    val=$(getprop "$prop" 2>/dev/null)
    if [ -n "$val" ]; then
      case "$val" in
        *V12*|*V13*|*V14*|*OS1*|*MIUI*|*HyperOS*) IS_MIUI=1; break ;;
      esac
    fi
  done
  
  if [ "$IS_MIUI" -eq 0 ]; then
    if [ -f "/system/build.prop" ]; then
      if grep -qi "miui" /system/build.prop 2>/dev/null; then
        IS_MIUI=1
      fi
    fi
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
# Locate DTBO block device
DTBO_BLK=""
for part in "dtbo_a" "dtbo_b" "dtbo"; do
  for path in "/dev/block/bootdevice/by-name/$part" "/dev/block/by-name/$part" "/dev/block/mapper/$part"; do
    if [ -b "$path" ] || [ -e "$path" ]; then
      DTBO_BLK="$path"
      break 2
    fi
  done
done

# 1. Backup current DTBO before first flashing
if [ -n "$DTBO_BLK" ] && [ ! -f /data/adb/munch_stock_dtbo.img ]; then
  ui_print "--> Backing up current DTBO..."
  dd if="$DTBO_BLK" of="/data/adb/munch_stock_dtbo.img" bs=4096 2>/dev/null
fi

ui_print " "
ui_print "--> Flashing 144Hz DTBO..."
FLASHED=0
for part in "dtbo_a" "dtbo_b" "dtbo"; do
  for path in "/dev/block/bootdevice/by-name/$part" "/dev/block/by-name/$part" "/dev/block/mapper/$part"; do
    if [ -b "$path" ] || [ -e "$path" ]; then
      ui_print "  Flashing to $part ($path)..."
      if dd if="$MODPATH/dtbo.img" of="$path" bs=4096 2>/dev/null; then
        FLASHED=1
      elif cat "$MODPATH/dtbo.img" > "$path" 2>/dev/null; then
        FLASHED=1
      fi
      break
    fi
  done
done

if [ "$FLASHED" -eq 1 ]; then
  ui_print "  [+] DTBO flashed successfully."
else
  ui_print "  [!] Notice: DTBO block device not found directly."
  ui_print "      Please also flash twrp_munch_144hz_display_unlock.zip in TWRP if DTBO was not written."
fi

ui_print " "
if [ "$TARGET_ROM" = "miui" ]; then
  ui_print "--> Configuring MIUI/HyperOS Display Settings..."
  ui_print "  [+] Systemless overlay applied to device_features/munch.xml"
  ui_print "  [+] 144Hz option enabled in Settings"
  ui_print "  [+] Idle-drop fix enabled"
else
  ui_print "--> Configuring AOSP..."
  ui_print "  [+] AOSP displays read 144Hz natively from DTBO timings."
  ui_print "  [*] Removing MIUI overlay to keep system 100% clean."
  rm -rf "$MODPATH/system"
fi

# Set executable permission for scripts
chmod 0755 "$MODPATH/service.sh" 2>/dev/null
chmod 0755 "$MODPATH/uninstall.sh" 2>/dev/null

ui_print " "
ui_print "--------------------------------------------------"
ui_print "  Installation completed successfully!            "
ui_print "  Please reboot your device.                      "
ui_print "--------------------------------------------------"
"""

# service.sh (Late-start background service: Auto-heals DTBO & prevents idle-drop)
service_sh = """#!/system/bin/sh
##########################################################################################
# POCO F4 (munch) 144Hz Auto-Guard & Refresh Rate Auto-Lock Service
# Author: fatidaprilian
##########################################################################################

MODDIR=${0%/*}

# Wait for boot completion
until [ "$(getprop sys.boot_completed)" = "1" ]; do
  sleep 2
done

# Wait 5s for system settling
sleep 5

# --- Part 1: Auto-Guard (Restore DTBO if overwritten by custom kernel) ---
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
        # Overwritten partition detected! Restore 144Hz DTBO
        for part in "dtbo_a" "dtbo_b" "dtbo"; do
          for path in "/dev/block/bootdevice/by-name/$part" "/dev/block/by-name/$part" "/dev/block/mapper/$part"; do
            if [ -b "$path" ] || [ -e "$path" ]; then
              dd if="$MODDIR/dtbo.img" of="$path" bs=4096 2>/dev/null
              break
            fi
          done
        done

        # Notify user that DTBO was restored and a restart is needed
        cmd notification post -S bigtext -t "POCO F4 144Hz" "Tag144" "Kernel update detected! 144Hz DTBO was automatically restored. Please restart your phone to apply." 2>/dev/null
      fi
      rm -f "$CHECK_TMP"
    fi
  fi
fi

# --- Part 2: 144Hz Settings Synchronizer & Zero Idle-Drop Daemon ---
# Android DisplayModeDirector idle timer drops refresh rate if min_refresh_rate is not synced.
# This daemon ensures min_refresh_rate tracks user_refresh_rate so 144Hz never drops when idle.
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

# uninstall.sh (Executes automatically when user removes the module in KernelSU/Magisk)
uninstall_sh = """#!/system/bin/sh
##########################################################################################
# POCO F4 (munch) 144Hz Display Mod Uninstaller
# Author: fatidaprilian
##########################################################################################

# 1. Restore factory stock DTBO if backup exists
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

# 2. Reset display settings database back to factory stock 120Hz
settings delete system min_refresh_rate 2>/dev/null
settings put system peak_refresh_rate 120.0 2>/dev/null
settings put system user_refresh_rate 120 2>/dev/null
"""

# Universal update-binary for Manager & Recovery
update_binary = """#!/sbin/sh
##########################################################################################
# Universal KernelSU / Magisk / APatch / Recovery Module Installer
# Author: fatidaprilian
##########################################################################################

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

mount /data 2>/dev/null

UTIL_PATH=""
if [ -f /data/adb/ksu/util_functions.sh ]; then
  UTIL_PATH="/data/adb/ksu/util_functions.sh"
elif [ -f /data/adb/magisk/util_functions.sh ]; then
  UTIL_PATH="/data/adb/magisk/util_functions.sh"
elif [ -f /data/adb/ap/util_functions.sh ]; then
  UTIL_PATH="/data/adb/ap/util_functions.sh"
fi

if [ -n "$UTIL_PATH" ]; then
  . "$UTIL_PATH"
  install_module
  exit 0
fi

# Direct Recovery Installation (TWRP fallback)
MODPATH="/data/adb/modules/munch_144hz_display_unlock"
mkdir -p "$MODPATH"
unzip -o "$ZIPFILE" -x 'META-INF/*' -d "$MODPATH" >/dev/null 2>&1
chmod -R 0755 "$MODPATH"

# Run customize script
if [ -f "$MODPATH/customize.sh" ]; then
  . "$MODPATH/customize.sh"
  rm -f "$MODPATH/customize.sh"
fi

find "$MODPATH" -type f -exec chmod 0644 {} + 2>/dev/null
chmod 0755 "$MODPATH/service.sh" 2>/dev/null
chmod 0755 "$MODPATH/uninstall.sh" 2>/dev/null
exit 0
"""

updater_script = "#MAGISK\n"

# Create ZIP
with zipfile.ZipFile(out_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    z.writestr('module.prop', module_prop)
    z.writestr('system.prop', system_prop)
    z.write(dtbo_img, 'dtbo.img')
    z.writestr('customize.sh', customize_sh)
    z.writestr('service.sh', service_sh)
    z.writestr('uninstall.sh', uninstall_sh)
    z.writestr('META-INF/com/google/android/update-binary', update_binary)
    z.writestr('META-INF/com/google/android/updater-script', updater_script)
    
    # Store patched xml for MIUI variants
    z.writestr('system/product/etc/device_features/munch.xml', patched_xml)
    z.writestr('system/product/etc/device_features/munch_global.xml', patched_xml)
    z.writestr('system/product/etc/device_features/munch_in.xml', patched_xml)

print(f"[+] Successfully built All-in-One Module with Auto-Guard & Clean Uninstaller: {out_zip} ({os.path.getsize(out_zip)} bytes)")

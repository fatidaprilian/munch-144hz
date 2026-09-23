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

# Patch values for MIUI/HyperOS
new_fps_list = """    <integer-array name="fpsList">
        <item>144</item>
        <item>120</item>
        <item>60</item>
    </integer-array>"""

patched_xml = xml_content.replace(
    '<integer name="smart_fps_value">120</integer>',
    '<integer name="smart_fps_value">144</integer>'
).replace(old_fps_list, new_fps_list)

print("[*] Successfully prepared patched munch.xml for MIUI/HyperOS")

# module.prop
module_prop = """id=munch_144hz_display_unlock
name=POCO F4 144Hz Calibration & Settings Unlock
version=v5.3-aio
versionCode=530
author=fatidaprilian
description=All-in-One installer: Flashes calibrated 144Hz DTBO (0-nit black, no scanlines, 1:1 brightness) & auto-guards against kernel overwrites.
"""

# customize.sh (Executed by KernelSU, Magisk, APatch, and TWRP direct installer)
customize_sh = """#!/sbin/sh
##########################################################################################
# POCO F4 (munch) 144Hz All-in-One Module Customization Script
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
ui_print "  POCO F4 (munch) 144Hz All-in-One Installer      "
ui_print "  Build v5.3: Calibrated DTBO & Settings Unlock   "
ui_print "  Author: fatidaprilian                           "
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
ui_print "--> Flashing Calibrated 144Hz DTBO..."
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
  ui_print "  [+] DTBO flashed successfully! (0-nit black, scanline-free, 1:1 brightness)"
else
  ui_print "  [!] Notice: DTBO block device not found directly."
  ui_print "      Please also flash twrp_144Munch_v5_3_parity26.zip in TWRP if DTBO was not written."
fi

ui_print " "
if [ "$TARGET_ROM" = "miui" ]; then
  ui_print "--> Configuring MIUI/HyperOS Display Settings..."
  ui_print "  [+] Systemless overlay applied to device_features/munch.xml"
  ui_print "  [+] 144Hz option enabled in Settings -> Display -> Refresh rate"
else
  ui_print "--> Configuring AOSP..."
  ui_print "  [+] AOSP displays read 144Hz natively from DTBO timings."
  ui_print "  [*] Removing MIUI overlay to keep system 100% clean."
  rm -rf "$MODPATH/system"
fi

# Set executable permission for background auto-guard service
chmod 0755 "$MODPATH/service.sh" 2>/dev/null

ui_print " "
ui_print "--------------------------------------------------"
ui_print "  Installation completed successfully!            "
ui_print "  Please reboot your device.                      "
ui_print "--------------------------------------------------"
"""

# service.sh (Late-start background service: Auto-heals DTBO if overwritten by custom kernels)
service_sh = """#!/system/bin/sh
##########################################################################################
# POCO F4 (munch) 144Hz Auto-Guard Service
# Author: fatidaprilian
##########################################################################################

MODDIR=${0%/*}

# Wait for boot completion
until [ "$(getprop sys.boot_completed)" = "1" ]; do
  sleep 2
done

# Wait 5s for system settling
sleep 5

[ -f "$MODDIR/dtbo.img" ] || exit 0

DTBO_BLK=""
for part in "dtbo_a" "dtbo_b" "dtbo"; do
  for path in "/dev/block/bootdevice/by-name/$part" "/dev/block/by-name/$part" "/dev/block/mapper/$part"; do
    if [ -b "$path" ] || [ -e "$path" ]; then
      DTBO_BLK="$path"
      break 2
    fi
  done
done

[ -n "$DTBO_BLK" ] || exit 0

DTBO_SIZE=$(wc -c < "$MODDIR/dtbo.img")
CHECK_TMP="/data/local/tmp/dtbo_check"

# Read payload size from partition
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
exit 0
"""

updater_script = "#MAGISK\n"

# Create ZIP
with zipfile.ZipFile(out_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    z.writestr('module.prop', module_prop)
    z.write(dtbo_img, 'dtbo.img')
    z.writestr('customize.sh', customize_sh)
    z.writestr('service.sh', service_sh)
    z.writestr('META-INF/com/google/android/update-binary', update_binary)
    z.writestr('META-INF/com/google/android/updater-script', updater_script)
    
    # Store patched xml for MIUI variants
    z.writestr('system/product/etc/device_features/munch.xml', patched_xml)
    z.writestr('system/product/etc/device_features/munch_global.xml', patched_xml)
    z.writestr('system/product/etc/device_features/munch_in.xml', patched_xml)

print(f"[+] Successfully built All-in-One Module with Auto-Guard: {out_zip} ({os.path.getsize(out_zip)} bytes)")

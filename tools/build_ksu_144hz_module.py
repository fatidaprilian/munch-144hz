import os, zipfile, shutil

# Paths
source_xml = '/home/ryuen/Project/munch-144hz/munch.xml'
out_dir = '/home/ryuen/Project/munch-144hz/out'
out_zip = os.path.join(out_dir, 'ksu_munch_144hz_display_unlock.zip')

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

# Patch values
new_fps_list = """    <integer-array name="fpsList">
        <item>144</item>
        <item>120</item>
        <item>60</item>
    </integer-array>"""

patched_xml = xml_content.replace(
    '<integer name="smart_fps_value">120</integer>',
    '<integer name="smart_fps_value">144</integer>'
).replace(old_fps_list, new_fps_list)

print("[*] Successfully patched munch.xml with 144Hz support")

# module.prop
module_prop = """id=munch_144hz_display_unlock
name=POCO F4 144Hz Display Settings Unlock
version=v1.0
versionCode=100
author=fatidaprilian
description=Unlocks native 144Hz refresh rate option in MIUI 13 / HyperOS Display Settings for POCO F4 (munch).
"""

# Universal KernelSU / Magisk / APatch / TWRP update-binary
update_binary = """#!/sbin/sh
##########################################################################################
# Universal KernelSU / Magisk / APatch / Recovery Module Installer
# Author: fatidaprilian
##########################################################################################

umask 022

# Arguments passed by manager / recovery
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
ui_print "    POCO F4 (munch) 144Hz Display Settings Unlock "
ui_print "    Author: fatidaprilian                         "
ui_print "    GitHub: github.com/fatidaprilian              "
ui_print "--------------------------------------------------"

mount /data 2>/dev/null

# Detect installation environment
UTIL_PATH=""
if [ -f /data/adb/ksu/util_functions.sh ]; then
  UTIL_PATH="/data/adb/ksu/util_functions.sh"
  ui_print "[*] Environment: KernelSU detected"
elif [ -f /data/adb/magisk/util_functions.sh ]; then
  UTIL_PATH="/data/adb/magisk/util_functions.sh"
  ui_print "[*] Environment: Magisk detected"
elif [ -f /data/adb/ap/util_functions.sh ]; then
  UTIL_PATH="/data/adb/ap/util_functions.sh"
  ui_print "[*] Environment: APatch detected"
fi

if [ -n "$UTIL_PATH" ]; then
  . "$UTIL_PATH"
  install_module
  exit 0
fi

# Fallback direct installation (for TWRP recovery without manager active)
ui_print "[*] Performing direct module extraction to /data/adb/modules..."
MOD_TARGET="/data/adb/modules/munch_144hz_display_unlock"
mkdir -p "$MOD_TARGET"
unzip -o "$ZIPFILE" -x 'META-INF/*' -d "$MOD_TARGET" >/dev/null 2>&1
chmod -R 0755 "$MOD_TARGET"
find "$MOD_TARGET" -type f -exec chmod 0644 {} +

ui_print "[+] Done! Module installed successfully."
ui_print "[+] Reboot your device to see 144Hz in Settings!"
ui_print "--------------------------------------------------"
exit 0
"""

updater_script = "#MAGISK\n"

# Create ZIP
with zipfile.ZipFile(out_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    z.writestr('module.prop', module_prop)
    z.writestr('META-INF/com/google/android/update-binary', update_binary)
    z.writestr('META-INF/com/google/android/updater-script', updater_script)
    
    # Store patched xml for all munch variants (munch, munch_global, munch_in)
    z.writestr('system/product/etc/device_features/munch.xml', patched_xml)
    z.writestr('system/product/etc/device_features/munch_global.xml', patched_xml)
    z.writestr('system/product/etc/device_features/munch_in.xml', patched_xml)

print(f"[+] Successfully built KernelSU module: {out_zip} ({os.path.getsize(out_zip)} bytes)")

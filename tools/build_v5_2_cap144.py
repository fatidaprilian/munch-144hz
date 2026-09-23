import os, struct, zipfile, subprocess, re

# Resolve root relative to this script (tools/../)
_root          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
orig_dtbo_path = os.path.join(_root, 'reference', 'unpacked_twrp_144munch', 'dtbo.img')
with open(orig_dtbo_path, 'rb') as f:
    data = bytearray(f.read())

dtb_start = data.find(b'\xd0\x0d\xfe\xed')
if dtb_start != 0x40:
    raise RuntimeError(f"Unexpected DTB start: 0x{dtb_start:x}")

print("==================================================")
print("--- BUILD v5.2: CAP TO 144Hz (164/167 -> 144Hz) ---")
print("==================================================")

# =========================================================================
# 1. Patch timing@3 (144Hz Mode)
# =========================================================================
# 1.1 transfer-time-us: 7000us -> 6000us (0x1b58 -> 0x1770)
tt3_off = dtb_start + 0x47ec8  # 0x47f08
curr_tt3 = struct.unpack('>I', data[tt3_off:tt3_off+4])[0]
if curr_tt3 != 0x1b58:
    raise RuntimeError(f"Expected 0x1b58 at 0x{tt3_off:x}, got 0x{curr_tt3:x}")
data[tt3_off:tt3_off+4] = struct.pack('>I', 0x1770)
print(f"[*] Patched timing@3 transfer-time-us at 0x{tt3_off:x}: 7000us -> 6000us")

# 1.2 v-front-porch: 580 -> 535 (0x244 -> 0x217) [Exact solid 144.0Hz hardware TE rate]
vfp3_off = 0x47e74
curr_vfp3 = struct.unpack('>I', data[vfp3_off:vfp3_off+4])[0]
if curr_vfp3 != 0x244:
    raise RuntimeError(f"Expected 0x244 at 0x{vfp3_off:x}, got 0x{curr_vfp3:x}")
data[vfp3_off:vfp3_off+4] = struct.pack('>I', 0x217)
print(f"[*] Patched timing@3 v-front-porch at 0x{vfp3_off:x}: 580 -> 535 [Exact 144.0Hz]")

# =========================================================================
# 2. Patch timing@4 (164Hz Mode -> 144Hz Capped Mode)
# So selecting 164/167 in any APK runs the exact stable 144Hz profile
# =========================================================================
# 2.1 panel-framerate: 164 -> 144 (0xa4 -> 0x90)
fr4_off = 0x48a1c
curr_fr4 = struct.unpack('>I', data[fr4_off:fr4_off+4])[0]
if curr_fr4 != 0xa4:
    raise RuntimeError(f"Expected 0xa4 at 0x{fr4_off:x}, got 0x{curr_fr4:x}")
data[fr4_off:fr4_off+4] = struct.pack('>I', 0x90)
print(f"[*] Patched timing@4 panel-framerate at 0x{fr4_off:x}: 164 (0xa4) -> 144 (0x90)")

# 2.2 v-back-porch: 613 -> 580 (0x265 -> 0x244)
vbp4_off = 0x48a8c
curr_vbp4 = struct.unpack('>I', data[vbp4_off:vbp4_off+4])[0]
if curr_vbp4 != 0x265:
    raise RuntimeError(f"Expected 0x265 at 0x{vbp4_off:x}, got 0x{curr_vbp4:x}")
data[vbp4_off:vbp4_off+4] = struct.pack('>I', 0x244)
print(f"[*] Patched timing@4 v-back-porch at 0x{vbp4_off:x}: 613 -> 580")

# 2.3 v-front-porch: 613 -> 535 (0x265 -> 0x217)
vfp4_off = 0x48a9c
curr_vfp4 = struct.unpack('>I', data[vfp4_off:vfp4_off+4])[0]
if curr_vfp4 != 0x265:
    raise RuntimeError(f"Expected 0x265 at 0x{vfp4_off:x}, got 0x{curr_vfp4:x}")
data[vfp4_off:vfp4_off+4] = struct.pack('>I', 0x217)
print(f"[*] Patched timing@4 v-front-porch at 0x{vfp4_off:x}: 613 -> 535 [Exact 144.0Hz]")

# 2.4 panel-clockrate: 1252777777 -> 1100000000 (0x4aabdf31 -> 0x4190ab00)
clk4_off = 0x48b0c
curr_clk4 = struct.unpack('>I', data[clk4_off:clk4_off+4])[0]
if curr_clk4 != 0x4aabdf31:
    raise RuntimeError(f"Expected 0x4aabdf31 at 0x{clk4_off:x}, got 0x{curr_clk4:x}")
data[clk4_off:clk4_off+4] = struct.pack('>I', 0x4190ab00)
print(f"[*] Patched timing@4 panel-clockrate at 0x{clk4_off:x}: 1252MHz -> 1100MHz")

# =========================================================================
# 3. Hardware Display Calibration (Native 255 KCAL Balance)
# =========================================================================
replacements = [
    # Gate voltage 14 & 99: 39 39 -> 41 41 (preserves stability, prevents scanlines)
    (bytes.fromhex('02b01439010000000003d33939'), bytes.fromhex('02b01439010000000003d34141')),
    (bytes.fromhex('02b09939010000000003d33939'), bytes.fromhex('02b09939010000000003d34141')),
    # Gamma reference 2a & 2e: 2c -> 27 (Native 255 tuning: eliminates non-black highlight lift)
    (bytes.fromhex('02b02a39000000000002d32c'), bytes.fromhex('02b02a39000000000002d327')),
    (bytes.fromhex('02b02e39000000000002d32c'), bytes.fromhex('02b02e39000000000002d327')),
    # Negative gamma reference af & b3: 18 -> 24 (Anchors near-black curve)
    (bytes.fromhex('02b0af39000000000002d318'), bytes.fromhex('02b0af39000000000002d324')),
    (bytes.fromhex('02b0b339000000000002d318'), bytes.fromhex('02b0b339000000000002d324')),
    # ELVSS cathode: 48 0e 48 0e -> 42 12 42 12 (0-nit OLED black)
    (bytes.fromhex('02b05f39010000000005d3480e480e'), bytes.fromhex('02b05f39010000000005d342124212')),
]

total_replaced = 0
for pat, rep in replacements:
    count = 0
    pos = 0
    while True:
        idx = data.find(pat, pos)
        if idx == -1:
            break
        data[idx:idx+len(pat)] = rep
        count += 1
        pos = idx + len(rep)
    print(f"[*] Replaced register pattern {pat[1:3].hex()}: {count} instances")
    total_replaced += count

print(f"\nTotal pattern blocks replaced: {total_replaced} (expected 42)")

# =========================================================================
# 4. Write Output DTBO & Package TWRP ZIP
# =========================================================================
out_dtbo   = os.path.join(_root, 'out', 'dtbo.img')
with open(out_dtbo, 'wb') as f:
    f.write(data)

out_zip    = os.path.join(_root, 'out', 'twrp_144Munch_v5_2_cap144.zip')
ref_binary = os.path.join(_root, 'reference', 'unpacked_twrp_144munch', 'META-INF', 'com', 'google', 'android', 'update-binary')

clean_updater_script = """ui_print("------------------------------------------------");
ui_print("        POCO F4 (munch) 144Hz Calibration       ");
ui_print("        Calibrated by: fatidaprilian            ");
ui_print("        GitHub: github.com/fatidaprilian        ");
ui_print("------------------------------------------------");
ui_print("[*] Flashing calibrated DTBO to dtbo_a...");
package_extract_file("dtbo.img", "/dev/block/bootdevice/by-name/dtbo_a");
ui_print("[*] Flashing calibrated DTBO to dtbo_b...");
package_extract_file("dtbo.img", "/dev/block/bootdevice/by-name/dtbo_b");
ui_print("[+] Done! 144Hz calibration applied successfully.");
ui_print("------------------------------------------------");
"""

with zipfile.ZipFile(out_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    z.write(out_dtbo, 'dtbo.img')
    z.write(ref_binary, 'META-INF/com/google/android/update-binary')
    z.writestr('META-INF/com/google/android/updater-script', clean_updater_script)

print(f"\n[+] Created flashable ZIP: {out_zip} ({os.path.getsize(out_zip)} bytes)")

# =========================================================================
# 5. Decompile and Verify with DTC
# =========================================================================
dtc_bin    = os.path.join(_root, 'tools', 'usr', 'bin', 'dtc')
dump_dtb   = os.path.join(_root, 'out', 'dump_v5_2.dtb')
with open(dump_dtb, 'wb') as f:
    f.write(data[0x40:])

verify_dts = os.path.join(_root, 'out', 'dump_v5_2.dts')
subprocess.run([dtc_bin, '-I', 'dtb', '-O', 'dts', dump_dtb, '-o', verify_dts], capture_output=True, text=True)

with open(verify_dts, 'r') as f:
    v_text = f.read()

pos = v_text.find('l11r_38_08_0a')
t3_start = v_text.find('timing@3 {', pos)
t4_start = v_text.find('timing@4 {', pos)
t4_end = v_text.find('qcom,display-topology', t4_start)

t3_text = v_text[t3_start:t4_start]
t4_text = v_text[t4_start:t4_end]

print("\n==================================================")
print("--- TIMING@3 (144Hz) VERIFICATION ---")
print("==================================================")
print("  Framerate:", re.search(r'panel-framerate\s*=\s*<([^>]+)>', t3_text).group(1), "(0x90 = 144Hz)")
print("  v-front-porch:", re.search(r'v-front-porch\s*=\s*<([^>]+)>', t3_text).group(1), "(0x217 = 535 lines -> Exact 144.0Hz solid)")
print("  v-back-porch:", re.search(r'v-back-porch\s*=\s*<([^>]+)>', t3_text).group(1), "(0x244 = 580 lines)")
print("  Clockrate:", re.search(r'panel-clockrate\s*=\s*<([^>]+)>', t3_text).group(1), "(0x4190ab00 = 1100MHz)")
print("  transfer-time-us:", re.search(r'transfer-time-us\s*=\s*<([^>]+)>', t3_text).group(1), "(0x1770 = 6000us)")

print("\n==================================================")
print("--- TIMING@4 (CAPPED 144Hz) VERIFICATION ---")
print("==================================================")
print("  Framerate:", re.search(r'panel-framerate\s*=\s*<([^>]+)>', t4_text).group(1), "(0x90 = 144Hz [CAPPED])")
print("  v-front-porch:", re.search(r'v-front-porch\s*=\s*<([^>]+)>', t4_text).group(1), "(0x217 = 535 lines -> Exact 144.0Hz solid)")
print("  v-back-porch:", re.search(r'v-back-porch\s*=\s*<([^>]+)>', t4_text).group(1), "(0x244 = 580 lines)")
print("  Clockrate:", re.search(r'panel-clockrate\s*=\s*<([^>]+)>', t4_text).group(1), "(0x4190ab00 = 1100MHz)")
print("  transfer-time-us:", re.search(r'transfer-time-us\s*=\s*<([^>]+)>', t4_text).group(1), "(0x1770 = 6000us)")

# Assert that timing@3 and timing@4 timing parameters are identical
for prop in ['panel-framerate', 'v-front-porch', 'v-back-porch', 'panel-clockrate', 'transfer-time-us']:
    val3 = re.search(prop + r'\s*=\s*<([^>]+)>', t3_text).group(1)
    val4 = re.search(prop + r'\s*=\s*<([^>]+)>', t4_text).group(1)
    if val3 != val4:
        raise AssertionError(f"Mismatch in {prop}: t3={val3} != t4={val4}")

print("\n[+] Verification SUCCESS: timing@3 and timing@4 are 100% harmonized to 144.0Hz!")

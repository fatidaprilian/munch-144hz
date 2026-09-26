#!/usr/bin/env python3
"""
POCO F4 (munch) 144Hz Display Mod Builder
Author: fatidaprilian
GitHub: https://github.com/fatidaprilian/munch-144hz
"""

import os
import shutil
import struct
import subprocess
import zipfile

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
stock_dtb_path = os.path.join(_root, 'reference', 'unpacked_munch', 'dtb_00_id_0x00000000.dtb')
mkdtbo_bin = os.path.join(_root, 'tools', 'mkdtbo.py')

out_dir = os.path.join(_root, 'out')
os.makedirs(out_dir, exist_ok=True)

tmp_dir = os.path.join(out_dir, 'build_tmp')
os.makedirs(tmp_dir, exist_ok=True)

print("[*] Injecting 144Hz timing into stock munch DTB...")

# 1. Read Stock Munch DTB
with open(stock_dtb_path, 'rb') as f:
    data = bytearray(f.read())

magic, totalsize, off_dt_struct, off_dt_strings, off_mem_rsvmap, version, last_comp_version, boot_cpuid_phys, size_dt_strings, size_dt_struct = struct.unpack(">10I", data[:40])

if magic != 0xd00dfeed:
    raise ValueError(f"Invalid DTB magic: {hex(magic)}")

strings_block = bytes(data[off_dt_strings:off_dt_strings + size_dt_strings])

def get_nameoff(prop_name):
    target = prop_name.encode("ascii") + b"\x00"
    pos = strings_block.find(target)
    if pos == -1:
        raise ValueError(f"String '{prop_name}' not found in dt_strings")
    return pos

def make_fdt_prop(name, value_bytes):
    nameoff = get_nameoff(name)
    plen = len(value_bytes)
    pad_len = (4 - (plen % 4)) % 4
    padded = value_bytes + (b"\x00" * pad_len)
    return struct.pack(">III", 3, plen, nameoff) + padded

# 2. Parse dt_struct to locate:
# - qcom,ulps-enabled in l11r
# - end of timing@1 in l11r
offset = off_dt_struct
end_offset = off_dt_struct + size_dt_struct

path = []
ulps_prop_range = None
timing1_end_offset = None

while offset < end_offset:
    tag = struct.unpack(">I", data[offset:offset+4])[0]
    token_start = offset
    offset += 4
    if tag == 1: # FDT_BEGIN_NODE
        name_end = data.find(b"\x00", offset)
        name = data[offset:name_end].decode("ascii")
        offset = (name_end + 1 + 3) & ~3
        path.append(name)
    elif tag == 2: # FDT_END_NODE
        full_path = "/" + "/".join(path[1:])
        if full_path == "/fragment@57/__overlay__/qcom,mdss_dsi_l11r_38_08_0a_dsc_cmd/qcom,mdss-dsi-display-timings/timing@1":
            timing1_end_offset = offset
        if path:
            path.pop()
    elif tag == 3: # FDT_PROP
        plen, nameoff = struct.unpack(">II", data[offset:offset+8])
        name_end = strings_block.find(b"\x00", nameoff)
        prop_name = strings_block[nameoff:name_end].decode("ascii")
        offset += 8
        full_path = "/" + "/".join(path[1:])
        if full_path == "/fragment@57/__overlay__/qcom,mdss_dsi_l11r_38_08_0a_dsc_cmd" and prop_name == "qcom,ulps-enabled":
            pad_len = (4 - (plen % 4)) % 4
            ulps_prop_range = (token_start, offset + plen + pad_len)
        offset = (offset + plen + 3) & ~3
    elif tag == 4: # FDT_NOP
        pass
    elif tag == 9: # FDT_END
        break

if not timing1_end_offset:
    raise RuntimeError("Could not find timing@1 in stock DTB")

# 3. Disable qcom,ulps-enabled using FDT_NOP
if ulps_prop_range:
    start, end = ulps_prop_range
    nop_count = (end - start) // 4
    data[start:end] = struct.pack(">I", 4) * nop_count

# 4. Build FDT tokens for timing@2 (144Hz)
t2_bytes = bytearray()
t2_bytes += struct.pack(">I", 1) + b"timing@2\x00\x00\x00\x00"

t2_bytes += make_fdt_prop("qcom,mdss-dsi-panel-framerate", struct.pack(">I", 144))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-panel-width", struct.pack(">I", 1080))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-panel-height", struct.pack(">I", 2400))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-h-front-porch", struct.pack(">I", 14))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-h-back-porch", struct.pack(">I", 10))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-h-pulse-width", struct.pack(">I", 6))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-h-sync-skew", struct.pack(">I", 0))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-v-back-porch", struct.pack(">I", 580))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-v-front-porch", struct.pack(">I", 580))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-v-pulse-width", struct.pack(">I", 32))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-h-sync-pulse", struct.pack(">I", 0))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-h-left-border", struct.pack(">I", 0))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-h-right-border", struct.pack(">I", 0))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-v-top-border", struct.pack(">I", 0))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-v-bottom-border", struct.pack(">I", 0))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-panel-clockrate", struct.pack(">I", 1100000000))
t2_bytes += make_fdt_prop("qcom,mdss-dsi-panel-jitter", struct.pack(">II", 5, 1))
t2_bytes += make_fdt_prop("qcom,mdss-mdp-transfer-time-us", struct.pack(">I", 7000))

# DSI Commands
on_cmd = bytes.fromhex("05 01 00 00 0a 00 02 11 00 39 01 00 00 00 00 02 35 00 39 01 00 00 00 00 02 9d 01 39 01 00 00 00 00 81 9e 11 00 00 89 30 80 09 60 04 38 00 08 02 1c 02 1c 02 00 02 0e 00 20 00 bb 00 07 00 0c 0d b7 0c b7 18 00 10 f0 03 0c 20 00 06 0b 0b 33 0e 1c 2a 38 46 54 62 69 70 77 79 7b 7d 7e 01 02 01 00 09 40 09 be 19 fc 19 fa 19 f8 1a 38 1a 78 1a b6 2a f6 2b 34 2b 74 3b 74 6b f4 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 39 00 00 00 00 00 05 2a 00 00 04 37 39 01 00 00 00 00 05 2b 00 00 09 5f 39 01 00 00 00 00 03 f0 5a 5a 39 00 00 00 00 00 02 b0 01 39 01 00 00 00 00 02 b7 4f 39 01 00 00 00 00 03 f0 a5 a5 39 01 00 00 00 00 03 f0 5a 5a 39 00 00 00 00 00 02 b0 02 39 00 00 00 00 00 05 ec 00 c0 c3 43 39 00 00 00 00 00 02 b0 0d 39 00 00 00 00 00 02 ec 19 39 00 00 00 00 00 02 b0 06 39 01 00 00 00 00 02 e4 d0 39 01 00 00 00 00 03 f0 a5 a5 39 01 00 00 00 00 03 f0 5a 5a 39 00 00 00 00 00 02 b0 36 39 00 00 00 00 00 02 d3 0f 39 00 00 00 00 00 02 f7 03 39 01 00 00 00 00 03 f0 a5 a5 39 01 00 00 00 00 03 f0 5a 5a 39 01 00 00 00 00 03 fc 5a 5a 39 00 00 00 00 00 02 b0 01 39 00 00 00 00 00 04 e4 a6 75 a3 39 01 00 00 00 00 0f e9 11 75 a6 75 a3 8d 06 20 8c a2 4e 00 32 32 39 01 00 00 00 00 03 fc a5 a5 39 01 00 00 00 00 03 f0 a5 a5 39 01 00 00 00 00 03 f0 5a 5a 39 00 00 00 00 00 04 df 83 00 10 39 00 00 00 00 00 02 b0 01 39 01 00 00 00 00 02 e6 01 39 01 00 00 00 00 03 f0 a5 a5 39 01 00 00 00 00 03 f0 5a 5a 39 00 00 00 00 00 02 b0 08 39 00 00 00 00 00 02 d4 05 39 01 00 00 00 00 03 f0 a5 a5 39 01 00 00 00 00 03 f0 5a 5a 39 01 00 00 00 00 03 fc 5a 5a 39 00 00 00 00 00 02 b0 16 39 01 00 00 00 00 02 d1 10 39 01 00 00 00 00 03 fc a5 a5 39 01 00 00 00 00 03 f0 a5 a5 39 01 00 00 00 00 03 f0 5a 5a 39 01 00 00 00 00 03 f1 5a 5a 39 01 00 00 00 00 03 fc 5a 5a 39 00 00 00 00 00 02 b0 14 39 01 00 00 00 00 03 d3 39 39 39 00 00 00 00 00 02 b0 2a 39 00 00 00 00 00 02 d3 2c 39 00 00 00 00 00 02 b0 2e 39 00 00 00 00 00 02 d3 2c 39 00 00 00 00 00 02 b0 5f 39 01 00 00 00 00 05 d3 48 0e 48 0e 39 00 00 00 00 00 02 b0 77 39 01 00 00 00 00 03 d3 04 47 39 00 00 00 00 00 02 b0 7b 39 01 00 00 00 00 03 d3 04 47 39 00 00 00 00 00 02 b0 99 39 01 00 00 00 00 03 d3 39 39 39 00 00 00 00 00 02 b0 af 39 00 00 00 00 00 02 d3 18 39 00 00 00 00 00 02 b0 b3 39 00 00 00 00 00 02 d3 18 39 00 00 00 00 00 02 f7 03 39 01 00 00 00 00 03 fc a5 a5 39 01 00 00 00 00 03 f1 a5 a5 39 01 00 00 5a 00 03 f0 a5 a5 39 01 00 00 00 00 03 f0 5a 5a 39 00 00 00 00 00 02 b0 06 39 00 00 00 00 00 02 b7 20 39 00 00 00 00 00 02 b0 05 39 01 00 00 00 00 02 b7 93 39 01 00 00 00 00 03 f0 a5 a5 39 01 00 00 00 00 02 53 20 39 01 00 00 00 00 03 51 00 00 05 01 00 00 00 00 02 29 00 39 01 00 00 00 00 02 60 10 39 01 00 00 00 00 03 f0 5a 5a 39 01 00 00 00 00 03 fc 5a 5a 39 00 00 00 00 00 02 b0 16 39 01 00 00 00 00 02 d1 10 39 01 00 00 00 00 03 fc a5 a5 39 01 00 00 00 00 03 f0 a5 a5")
t2_bytes += make_fdt_prop("qcom,mdss-dsi-on-command", on_cmd)

off_cmd = bytes.fromhex("05 01 00 00 14 00 02 28 00 39 01 00 00 00 00 02 53 20 05 01 00 00 78 00 02 10 00")
t2_bytes += make_fdt_prop("qcom,mdss-dsi-off-command", off_cmd)
t2_bytes += make_fdt_prop("qcom,mdss-dsi-on-command-state", b"dsi_lp_mode\x00")
t2_bytes += make_fdt_prop("qcom,mdss-dsi-off-command-state", b"dsi_lp_mode\x00")

switch_cmd = bytes.fromhex("39 01 00 00 00 00 03 f0 5a 5a 39 01 00 00 00 00 03 f1 5a 5a 39 01 00 00 00 00 03 fc 5a 5a 39 00 00 00 00 00 02 b0 14 39 01 00 00 00 00 03 d3 39 39 39 00 00 00 00 00 02 b0 2a 39 00 00 00 00 00 02 d3 2c 39 00 00 00 00 00 02 b0 2e 39 00 00 00 00 00 02 d3 2c 39 00 00 00 00 00 02 b0 5f 39 01 00 00 00 00 05 d3 48 0e 48 0e 39 00 00 00 00 00 02 b0 77 39 01 00 00 00 00 03 d3 04 47 39 00 00 00 00 00 02 b0 7b 39 01 00 00 00 00 03 d3 04 47 39 00 00 00 00 00 02 b0 99 39 01 00 00 00 00 03 d3 39 39 39 00 00 00 00 00 02 b0 af 39 00 00 00 00 00 02 d3 18 39 00 00 00 00 00 02 b0 b3 39 00 00 00 00 00 02 d3 18 39 00 00 00 00 00 02 f7 03 39 01 00 00 00 00 03 fc a5 a5 39 01 00 00 00 00 03 f1 a5 a5 39 01 00 00 23 00 03 f0 a5 a5 39 00 00 00 00 00 02 60 10 39 01 00 00 00 00 03 f0 5a 5a 39 01 00 00 00 00 03 fc 5a 5a 39 00 00 00 00 00 02 b0 16 39 00 00 00 00 00 02 d1 10 39 01 00 00 00 00 03 fc a5 a5 39 01 00 00 00 00 03 f0 a5 a5")
t2_bytes += make_fdt_prop("qcom,mdss-dsi-timing-switch-command", switch_cmd)
t2_bytes += make_fdt_prop("qcom,mdss-dsi-timing-switch-command-state", b"dsi_lp_mode\x00")

nolp_cmd = bytes.fromhex("39 01 00 00 00 00 03 f0 5a 5a 39 00 00 00 00 00 02 b0 0a 39 00 00 00 00 00 02 ee 06 39 00 00 00 00 00 02 b0 0b 39 00 00 00 00 00 03 d8 59 70 39 00 00 00 00 00 02 60 10 39 00 00 00 00 00 03 fc 5a 5a 39 00 00 00 00 00 02 b0 16 39 00 00 00 00 00 02 d1 10 39 00 00 00 00 00 03 fc a5 a5 39 01 00 00 00 00 02 53 28 39 01 00 00 09 00 03 f0 a5 a5")
t2_bytes += make_fdt_prop("qcom,mdss-dsi-nolp-command", nolp_cmd)
t2_bytes += make_fdt_prop("qcom,mdss-dsi-nolp-command-state", b"dsi_lp_mode\x00")

# Compression Mode & DSC
t2_bytes += make_fdt_prop("qcom,compression-mode", b"dsc\x00")
t2_bytes += make_fdt_prop("qcom,mdss-dsc-slice-height", struct.pack(">I", 8))
t2_bytes += make_fdt_prop("qcom,mdss-dsc-slice-width", struct.pack(">I", 540))
t2_bytes += make_fdt_prop("qcom,mdss-dsc-slice-per-pkt", struct.pack(">I", 2))
t2_bytes += make_fdt_prop("qcom,mdss-dsc-bit-per-component", struct.pack(">I", 8))
t2_bytes += make_fdt_prop("qcom,mdss-dsc-bit-per-pixel", struct.pack(">I", 8))
t2_bytes += make_fdt_prop("qcom,mdss-dsc-block-prediction-enable", b"")

# Xiaomi Extensions
t2_bytes += make_fdt_prop("mi,mdss-dsi-dimmingon-command", bytes.fromhex("39 01 00 00 00 00 02 53 28"))
t2_bytes += make_fdt_prop("mi,mdss-dsi-dimmingon-command-state", b"dsi_hs_mode\x00")
t2_bytes += make_fdt_prop("mi,mdss-dsi-dimmingoff-command", bytes.fromhex("39 01 00 00 00 00 02 53 20"))
t2_bytes += make_fdt_prop("mi,mdss-dsi-dimmingoff-command-state", b"dsi_hs_mode\x00")
t2_bytes += make_fdt_prop("mi,mdss-dsi-hbm-on-command", bytes.fromhex("39 01 00 00 00 00 02 53 e8 39 01 00 00 00 00 03 51 07 ff"))
t2_bytes += make_fdt_prop("mi,mdss-dsi-hbm-off-command", bytes.fromhex("39 01 00 00 00 00 02 53 28 39 01 00 00 00 00 03 51 07 ff"))
t2_bytes += make_fdt_prop("mi,mdss-dsi-hbm-on-command-state", b"dsi_lp_mode\x00")
t2_bytes += make_fdt_prop("mi,mdss-dsi-hbm-off-command-state", b"dsi_lp_mode\x00")

doze_hbm = bytes.fromhex("05 01 00 00 00 00 02 28 00 39 00 00 00 00 00 03 f0 5a 5a 39 00 00 00 00 00 02 60 00 39 00 00 00 00 00 03 fc 5a 5a 39 00 00 00 00 00 02 b0 16 39 00 00 00 00 00 02 d1 2e 39 00 00 00 00 00 03 fc a5 a5 39 00 00 00 00 00 02 b0 0b 39 00 00 00 00 00 03 d8 50 00 39 00 00 00 00 00 02 53 22 39 01 00 00 22 00 03 f0 a5 a5 05 01 00 00 00 00 02 29 00")
t2_bytes += make_fdt_prop("mi,mdss-dsi-doze-hbm-command", doze_hbm)
doze_lbm = bytes.fromhex("05 01 00 00 00 00 02 28 00 39 00 00 00 00 00 03 f0 5a 5a 39 00 00 00 00 00 02 60 00 39 00 00 00 00 00 03 fc 5a 5a 39 00 00 00 00 00 02 b0 16 39 00 00 00 00 00 02 d1 2e 39 00 00 00 00 00 03 fc a5 a5 39 00 00 00 00 00 02 b0 0b 39 00 00 00 00 00 03 d8 50 00 39 00 00 00 00 00 02 53 23 39 01 00 00 22 00 03 f0 a5 a5 05 01 00 00 00 00 02 29 00")
t2_bytes += make_fdt_prop("mi,mdss-dsi-doze-lbm-command", doze_lbm)
t2_bytes += make_fdt_prop("mi,mdss-dsi-doze-hbm-command-state", b"dsi_lp_mode\x00")
t2_bytes += make_fdt_prop("mi,mdss-dsi-doze-lbm-command-state", b"dsi_lp_mode\x00")

flat_on = bytes.fromhex("39 00 00 00 00 00 03 f0 5a 5a 39 00 00 00 00 00 03 c2 2d 27 39 00 00 00 00 00 0f e0 82 13 13 13 86 fc 08 80 00 00 00 00 ff 90 39 00 00 00 00 00 02 f7 03 39 01 00 00 09 00 03 f0 a5 a5")
t2_bytes += make_fdt_prop("mi,mdss-dsi-flat-on-command", flat_on)
flat_off = bytes.fromhex("39 00 00 00 00 00 03 f0 5a 5a 39 00 00 00 00 00 03 c2 2d 07 39 00 00 00 00 00 02 e0 00 39 00 00 00 00 00 02 f7 03 39 01 00 00 09 00 03 f0 a5 a5")
t2_bytes += make_fdt_prop("mi,mdss-dsi-flat-off-command", flat_off)
t2_bytes += make_fdt_prop("mi,mdss-dsi-flat-on-command-state", b"dsi_lp_mode\x00")
t2_bytes += make_fdt_prop("mi,mdss-dsi-flat-off-command-state", b"dsi_lp_mode\x00")

crc_off = bytes.fromhex("39 01 00 00 00 00 02 81 00 39 00 00 00 00 00 03 f0 5a 5a 39 00 00 00 00 00 02 b1 01 39 01 00 00 00 00 03 f0 a5 a5")
t2_bytes += make_fdt_prop("mi,mdss-dsi-crc-off-command", crc_off)
t2_bytes += make_fdt_prop("mi,mdss-dsi-crc-off-command-state", b"dsi_hs_mode\x00")

# SDE Display PHY Timings & Topology
phy_timings = bytes.fromhex("00 24 0a 0a 1a 19 09 0a 09 02 04 00 1e 0f")
t2_bytes += make_fdt_prop("qcom,mdss-dsi-panel-phy-timings", phy_timings)
t2_bytes += make_fdt_prop("qcom,display-topology", struct.pack(">III", 1, 1, 1))
t2_bytes += make_fdt_prop("qcom,default-topology-index", struct.pack(">I", 0))

# End Node
t2_bytes += struct.pack(">I", 2)

# 5. Insert timing@2 into data right after timing@1
insert_pos = timing1_end_offset
data_new = data[:insert_pos] + t2_bytes + data[insert_pos:]

# 6. Update FDT Header
delta = len(t2_bytes)
new_totalsize = totalsize + delta
new_size_dt_struct = size_dt_struct + delta
new_off_dt_strings = off_dt_strings + delta

struct.pack_into(">I", data_new, 4, new_totalsize)
struct.pack_into(">I", data_new, 12, new_off_dt_strings)
struct.pack_into(">I", data_new, 36, new_size_dt_struct)

injected_dtb = os.path.join(tmp_dir, 'dtb_00_id_0x00000000.dtb')
with open(injected_dtb, "wb") as f:
    f.write(data_new)

# 7. Pack into DTBO image
out_dtbo = os.path.join(out_dir, 'dtbo.img')
subprocess.run(['python3', mkdtbo_bin, 'create', out_dtbo, injected_dtb], check=True, stdout=subprocess.DEVNULL)

# 8. Prepare Patched munch.xml
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
    '<integer name="defaultFps">120</integer>'
)

# 9. Build Stock DTBO Image for module package
out_stock_dtbo = os.path.join(tmp_dir, 'stock_dtbo.img')
subprocess.run(['python3', mkdtbo_bin, 'create', out_stock_dtbo, stock_dtb_path], check=True, stdout=subprocess.DEVNULL)

# Helpers for ZIP packaging
def add_zip_entry(z, filename, data, mode=0o644):
    zinfo = zipfile.ZipInfo(filename)
    zinfo.date_time = (2026, 1, 1, 0, 0, 0)
    zinfo.external_attr = (0o100000 | mode) << 16
    zinfo.compress_type = zipfile.ZIP_DEFLATED
    if isinstance(data, str):
        data = data.encode('utf-8')
    z.writestr(zinfo, data)

def add_zip_file(z, arcname, filepath, mode=0o644):
    with open(filepath, 'rb') as f:
        content = f.read()
    add_zip_entry(z, arcname, content, mode=mode)

# Package Metadata
module_prop = """id=munch_144hz_display_unlock
name=POCO F4 144Hz Display Mod
version=v1.1.0
versionCode=150
author=fatidaprilian
description=Enables 144Hz display mode and restores factory stock DTBO on uninstallation.
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
sleep 3

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
MODDIR="${0%/*}"

STOCK_IMG=""
if [ -f "$MODDIR/stock_dtbo.img" ]; then
  STOCK_IMG="$MODDIR/stock_dtbo.img"
elif [ -f "/data/adb/munch_stock_dtbo.img" ]; then
  STOCK_IMG="/data/adb/munch_stock_dtbo.img"
fi

if [ -n "$STOCK_IMG" ] && [ -f "$STOCK_IMG" ]; then
  for part in "dtbo_a" "dtbo_b" "dtbo"; do
    for path in \
      "/dev/block/bootdevice/by-name/$part" \
      "/dev/block/by-name/$part" \
      "/dev/block/mapper/$part" \
      $(find /dev/block -iname "$part" 2>/dev/null); do
      if [ -b "$path" ]; then
        dd if="$STOCK_IMG" of="$path" bs=4096 2>/dev/null
        break
      fi
    done
  done
fi

settings delete system min_refresh_rate 2>/dev/null
settings put system peak_refresh_rate 120.0 2>/dev/null
settings put system user_refresh_rate 120 2>/dev/null
rm -f /data/adb/munch_stock_dtbo.img 2>/dev/null
exit 0
"""

post_fs_data_sh = """#!/system/bin/sh
MODDIR="${0%/*}"

if [ -f "$MODDIR/remove" ]; then
  if [ -f "$MODDIR/uninstall.sh" ]; then
    sh "$MODDIR/uninstall.sh"
  fi
fi
"""

action_sh = """#!/system/bin/sh
echo "POCO F4 144Hz Display Mod"
echo "Author: fatidaprilian"
echo "GitHub: https://github.com/fatidaprilian/munch-144hz"
echo "Current refresh rate:"
dumpsys display | grep -E "mCurrentRefreshRate|mBaseDisplayInfo" | head -n 3
"""

customize_sh = """#!/sbin/sh
ui_print "- POCO F4 (munch) 144Hz Display Mod"
ui_print "- Author: fatidaprilian"
ui_print "- GitHub: https://github.com/fatidaprilian/munch-144hz"

if [ -f "$MODPATH/stock_dtbo.img" ]; then
  mkdir -p /data/adb 2>/dev/null
  cp -f "$MODPATH/stock_dtbo.img" /data/adb/munch_stock_dtbo.img 2>/dev/null
fi

FLASHED=0
for part in "dtbo_a" "dtbo_b" "dtbo"; do
  for path in \
    "/dev/block/bootdevice/by-name/$part" \
    "/dev/block/by-name/$part" \
    "/dev/block/mapper/$part" \
    $(find /dev/block -iname "$part" 2>/dev/null); do
    if [ -b "$path" ]; then
      ui_print "- Flashing 144Hz DTBO to $path..."
      dd if="$MODPATH/dtbo.img" of="$path" bs=4096 2>/dev/null
      FLASHED=1
      break
    fi
  done
done

if [ "$FLASHED" -eq 1 ]; then
  ui_print "- DTBO flashed successfully."
else
  ui_print "! Warning: DTBO partition not found."
fi

set_perm_recursive "$MODPATH" 0 0 0755 0644
chmod 0755 "$MODPATH/uninstall.sh" "$MODPATH/service.sh" "$MODPATH/post-fs-data.sh" "$MODPATH/action.sh" 2>/dev/null
ui_print "- Done. Please reboot."
"""

# 10. Build KernelSU / Magisk / APatch Module ZIP
ksu_zip = os.path.join(out_dir, 'ksu_munch_144hz_display_unlock.zip')
with zipfile.ZipFile(ksu_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    add_zip_file(z, 'dtbo.img', out_dtbo, mode=0o644)
    add_zip_file(z, 'stock_dtbo.img', out_stock_dtbo, mode=0o644)
    add_zip_entry(z, 'module.prop', module_prop, mode=0o644)
    add_zip_entry(z, 'system.prop', system_prop, mode=0o644)
    add_zip_entry(z, 'service.sh', service_sh, mode=0o755)
    add_zip_entry(z, 'uninstall.sh', uninstall_sh, mode=0o755)
    add_zip_entry(z, 'post-fs-data.sh', post_fs_data_sh, mode=0o755)
    add_zip_entry(z, 'action.sh', action_sh, mode=0o755)
    add_zip_entry(z, 'customize.sh', customize_sh, mode=0o755)
    add_zip_entry(z, 'system/product/etc/device_features/munch.xml', patched_xml, mode=0o644)
    add_zip_entry(z, 'system/product/etc/device_features/munch_global.xml', patched_xml, mode=0o644)
    add_zip_entry(z, 'system/product/etc/device_features/munch_in.xml', patched_xml, mode=0o644)

# 11. TWRP Flasher Script
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

ui_print "- POCO F4 (munch) 144Hz Display Mod"
ui_print "- Author: fatidaprilian"
ui_print "- GitHub: https://github.com/fatidaprilian/munch-144hz"

mount /data 2>/dev/null

if [ ! -f /data/adb/munch_stock_dtbo.img ]; then
  mkdir -p /data/adb 2>/dev/null
  unzip -p "$ZIPFILE" stock_dtbo.img > /data/adb/munch_stock_dtbo.img 2>/dev/null
fi

FLASHED=0
for part in "dtbo_a" "dtbo_b" "dtbo"; do
  for path in \
    "/dev/block/bootdevice/by-name/$part" \
    "/dev/block/by-name/$part" \
    "/dev/block/mapper/$part" \
    $(find /dev/block -iname "$part" 2>/dev/null); do
    if [ -b "$path" ]; then
      unzip -p "$ZIPFILE" dtbo.img > "$path" 2>/dev/null && FLASHED=1
      break
    fi
  done
done

if [ "$FLASHED" -eq 1 ]; then
  ui_print "- DTBO flashed successfully."
fi

if [ -d /data/adb/modules ] || [ -d /data/adb/ksu ] || [ -d /data/adb/magisk ] || [ -d /data/adb/ap ]; then
  MODPATH="/data/adb/modules/munch_144hz_display_unlock"
  mkdir -p "$MODPATH"
  unzip -o "$ZIPFILE" -x 'META-INF/*' -d "$MODPATH" >/dev/null 2>&1
  chmod -R 0755 "$MODPATH"
  find "$MODPATH" -type f -exec chmod 0644 {} + 2>/dev/null
  chmod 0755 "$MODPATH/service.sh" "$MODPATH/uninstall.sh" "$MODPATH/post-fs-data.sh" "$MODPATH/action.sh" 2>/dev/null
  ui_print "- Module files installed to /data/adb/modules."
fi

ui_print "- Done. Please reboot."
exit 0
"""

twrp_zip = os.path.join(out_dir, 'twrp_munch_144hz_display_unlock.zip')
with zipfile.ZipFile(twrp_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    add_zip_file(z, 'dtbo.img', out_dtbo, mode=0o644)
    add_zip_file(z, 'stock_dtbo.img', out_stock_dtbo, mode=0o644)
    add_zip_entry(z, 'module.prop', module_prop, mode=0o644)
    add_zip_entry(z, 'system.prop', system_prop, mode=0o644)
    add_zip_entry(z, 'service.sh', service_sh, mode=0o755)
    add_zip_entry(z, 'uninstall.sh', uninstall_sh, mode=0o755)
    add_zip_entry(z, 'post-fs-data.sh', post_fs_data_sh, mode=0o755)
    add_zip_entry(z, 'action.sh', action_sh, mode=0o755)
    add_zip_entry(z, 'system/product/etc/device_features/munch.xml', patched_xml, mode=0o644)
    add_zip_entry(z, 'system/product/etc/device_features/munch_global.xml', patched_xml, mode=0o644)
    add_zip_entry(z, 'system/product/etc/device_features/munch_in.xml', patched_xml, mode=0o644)
    add_zip_entry(z, 'META-INF/com/google/android/update-binary', twrp_install_sh, mode=0o755)
    add_zip_entry(z, 'META-INF/com/google/android/updater-script', '#TWRP\n', mode=0o644)

# Clean up tmp
shutil.rmtree(tmp_dir, ignore_errors=True)

print(f"[+] Output DTBO: {out_dtbo}")
print(f"[+] Output KSU ZIP: {ksu_zip}")
print(f"[+] Output TWRP ZIP: {twrp_zip}")
print("[+] Build completed successfully.")

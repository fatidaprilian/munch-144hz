#!/usr/bin/env python3
"""
mkdtbo.py - Tool to inspect, unpack, and repack Android DTBO images.
Compatible with AOSP / Qualcomm libufdt format.
"""

import sys
import os
import struct
import argparse

DTBO_MAGIC = 0xD7B7AB1E
HEADER_FORMAT = '>IIIIIIII'
HEADER_SIZE = 32
ENTRY_FORMAT = '>IIIIIIII'
ENTRY_SIZE = 32

def dump_dtbo(image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    with open(image_path, 'rb') as f:
        header_data = f.read(HEADER_SIZE)
        if len(header_data) < HEADER_SIZE:
            print(f"Error: File {image_path} too small.")
            return False

        magic, total_size, header_size, dt_entry_size, dt_entry_count, dt_entries_offset, page_size, version = struct.unpack(HEADER_FORMAT, header_data)
        if magic != DTBO_MAGIC:
            print(f"Error: Invalid magic 0x{magic:08X} (expected 0x{DTBO_MAGIC:08X})")
            return False

        print(f"DTBO Image Header:")
        print(f"  Total Size:        {total_size} bytes")
        print(f"  Header Size:       {header_size}")
        print(f"  DT Entry Size:     {dt_entry_size}")
        print(f"  DT Entry Count:    {dt_entry_count}")
        print(f"  DT Entries Offset: {dt_entries_offset}")
        print(f"  Page Size:         {page_size}")
        print(f"  Version:           {version}\n")

        entries = []
        f.seek(dt_entries_offset)
        for i in range(dt_entry_count):
            entry_data = f.read(dt_entry_size)
            dt_size, dt_offset, dt_id, dt_rev, c0, c1, c2, c3 = struct.unpack(ENTRY_FORMAT, entry_data[:32])
            entries.append({
                'index': i,
                'size': dt_size,
                'offset': dt_offset,
                'id': dt_id,
                'rev': dt_rev,
                'custom': [c0, c1, c2, c3]
            })

        print(f"{'Idx':<4} {'Offset':<10} {'Size':<10} {'ID':<12} {'Rev':<10} {'Custom [0..3]'}")
        print("-" * 65)
        for e in entries:
            f.seek(e['offset'])
            dt_data = f.read(e['size'])
            out_file = os.path.join(output_dir, f"dtb_{e['index']:02d}_id_0x{e['id']:08x}.dtb")
            with open(out_file, 'wb') as out_f:
                out_f.write(dt_data)

            custom_str = " ".join([f"0x{x:08x}" for x in e['custom']])
            print(f"{e['index']:<4} 0x{e['offset']:<8x} {e['size']:<10} 0x{e['id']:<10x} 0x{e['rev']:<8x} {custom_str}")

        print(f"\nExtracted {dt_entry_count} DTB files to {output_dir}")
        return True

def create_dtbo(output_path, dtb_list, page_size=4096):
    entry_count = len(dtb_list)
    dt_entries_offset = HEADER_SIZE
    header_size = HEADER_SIZE
    dt_entry_size = ENTRY_SIZE
    
    # In Xiaomi / Qualcomm standard, DT entries start right after the table
    current_offset = dt_entries_offset + (entry_count * dt_entry_size)
    dt_entries = []
    dt_payloads = []
    
    for item in dtb_list:
        dtb_file, dt_id, dt_rev, custom = item
        with open(dtb_file, 'rb') as f:
            data = f.read()
        
        size = len(data)
        dt_entries.append((size, current_offset, dt_id, dt_rev, custom[0], custom[1], custom[2], custom[3]))
        dt_payloads.append((current_offset, data))
        current_offset += size
        
    total_size = current_offset
    
    with open(output_path, 'wb') as out_f:
        # Write header
        header = struct.pack(HEADER_FORMAT, DTBO_MAGIC, total_size, header_size, dt_entry_size, entry_count, dt_entries_offset, page_size, 0)
        out_f.write(header)
        
        # Write entry table
        for e in dt_entries:
            out_f.write(struct.pack(ENTRY_FORMAT, *e))
            
        # Write payloads
        for offset, data in dt_payloads:
            out_f.seek(offset)
            out_f.write(data)
            
    print(f"Created DTBO image {output_path} ({total_size} bytes, {entry_count} entries)")
    return True

def main():
    parser = argparse.ArgumentParser(description="DTBO image tool for Android/Qualcomm")
    subparsers = parser.add_subparsers(dest="command")

    dump_parser = subparsers.add_parser("dump", help="Dump/unpack DTBO image")
    dump_parser.add_argument("image", help="Path to dtbo.img")
    dump_parser.add_argument("-o", "--output", default="unpacked_dtbo", help="Output directory")

    create_parser = subparsers.add_parser("create", help="Create/pack DTBO image")
    create_parser.add_argument("output", help="Path to output dtbo.img")
    create_parser.add_argument("--page-size", type=int, default=4096, help="Page size (default: 4096)")
    create_parser.add_argument("dtbs", nargs="+", help="DTB files")

    args = parser.parse_args()
    if args.command == "dump":
        dump_dtbo(args.image, args.output)
    elif args.command == "create":
        dtb_list = [(f, 0, 0, [0, 0, 0, 0]) for f in args.dtbs]
        create_dtbo(args.output, dtb_list, args.page_size)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

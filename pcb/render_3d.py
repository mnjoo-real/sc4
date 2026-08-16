#!/usr/bin/env python3
"""Step 7: real KiCad 3D renders for every variant, via `kicad-cli pcb render`.

Usage:
    python3 render_3d.py
"""

import os
import subprocess
import sys

PCB_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PCB_DIR)
from generate_pcb import VARIANTS

KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def render_variant(variant):
    pcb_path = os.path.join(PCB_DIR, variant, f"{variant}.kicad_pcb")
    out_dir = os.path.join(PCB_DIR, variant, "renders")
    os.makedirs(out_dir, exist_ok=True)
    results = {}

    jobs = [
        ("top", ["--side", "top"]),
        ("bottom", ["--side", "bottom"]),
        ("perspective", ["--side", "top", "--perspective", "--rotate", "-30,0,20", "--zoom", "1.3"]),
    ]
    for label, extra_args in jobs:
        out_path = os.path.join(out_dir, f"{variant}_{label}.png")
        rc, out, err = run([
            KICAD_CLI, "pcb", "render", pcb_path,
            "--output", out_path,
            "--quality", "high", "--floor",
            "--width", "1600", "--height", "900",
        ] + extra_args)
        ok = rc == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 1000
        results[label] = ok
    return results


def main():
    all_ok = True
    for variant in VARIANTS:
        print(f"=== {variant} ===")
        results = render_variant(variant)
        for label, ok in results.items():
            print(f"  [{'OK' if ok else 'FAILED'}] {label}")
            all_ok = all_ok and ok
    print("ALL RENDERS OK" if all_ok else "SOME RENDERS FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

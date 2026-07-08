from __future__ import annotations

import argparse
import json
import math
import statistics
import time

import requests


def fiducials(data):
    results = data.get("Results", data)
    fid = results.get("Fiducial") or results.get("Fiducials") or []
    return fid if isinstance(fid, list) else [fid]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limelight-url", default="http://172.29.0.1:5807/results")
    parser.add_argument("--tag-id", type=int, default=0)
    parser.add_argument("--seconds", type=float, default=30.0)
    parser.add_argument("--timeout", type=float, default=0.25)
    args = parser.parse_args()
    deadline = time.time() + args.seconds
    poses = []
    while time.time() < deadline:
        try:
            data = requests.get(args.limelight_url, timeout=args.timeout).json()
            for f in fiducials(data):
                if int(f.get("fID", -1)) == args.tag_id:
                    pose = f.get("t6t_cs") or f.get("t6c_ts") or f.get("t6r_fs")
                    if pose and len(pose) >= 6:
                        poses.append([float(v) for v in pose[:6]])
        except Exception:
            pass
        time.sleep(0.05)
    if len(poses) < 3:
        print(json.dumps({"error": "not enough samples", "samples": len(poses)}, indent=2))
        return
    xs, ys, zs = zip(*[(p[0], p[1], p[2]) for p in poses], strict=False)
    rolls, pitches, yaws = zip(*[(p[3], p[4], p[5]) for p in poses], strict=False)
    pos_std = max(statistics.pstdev(xs), statistics.pstdev(ys), statistics.pstdev(zs))
    rot_std = max(statistics.pstdev(rolls), statistics.pstdev(pitches), statistics.pstdev(yaws))
    print(json.dumps({"position_std_m": pos_std, "rotation_std_deg": rot_std, "samples": len(poses)}, indent=2))


if __name__ == "__main__":
    main()

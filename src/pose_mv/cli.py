from __future__ import annotations

import argparse
from pathlib import Path

from .core import ingest, read_project
from .render import contact, render


def main():
    parser = argparse.ArgumentParser(description="Human-reviewed pose sheet animation; image generation is external")
    commands = parser.add_subparsers(dest="action", required=True)
    check = commands.add_parser("check")
    check.add_argument("project", type=Path)
    split = commands.add_parser("ingest")
    split.add_argument("sheet", type=Path)
    split.add_argument("mapping", type=Path)
    split.add_argument("output", type=Path)
    movie = commands.add_parser("render")
    movie.add_argument("project", type=Path)
    movie.add_argument("output", type=Path)
    movie.add_argument("--backend", choices=["rife", "hold"], required=True)
    movie.add_argument("--ffmpeg", default="ffmpeg")
    movie.add_argument("--comfy-root", type=Path)
    movie.add_argument("--weights", type=Path)
    movie.add_argument("--device", default="cuda")
    sheet = commands.add_parser("contact")
    sheet.add_argument("video", type=Path)
    sheet.add_argument("output", type=Path)
    sheet.add_argument("--every", type=int, default=6)
    args = parser.parse_args()
    if args.action == "check":
        data, root = read_project(args.project)
        for key in data["keys"]:
            if not (root / key["file"]).is_file():
                parser.error(f"Missing drawing: {key['file']}")
        print(f"Validated {len(data['keys'])} explicit keys")
    elif args.action == "ingest":
        print(f"Ingested {len(ingest(args.sheet, args.mapping, args.output))} drawings")
    elif args.action == "render":
        receipt = render(args.project, args.output, args.ffmpeg, args.backend, args.comfy_root, args.weights, args.device)
        print(f"Validated {receipt['frames']} decoded frames")
    elif args.action == "contact":
        contact(args.video, args.output, args.every)


if __name__ == "__main__":
    main()

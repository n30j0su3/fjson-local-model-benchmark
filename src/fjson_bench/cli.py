import argparse
import json
from pathlib import Path
from .gallery import export_pack
from .publish import build_public_pack
from .report import generate_report
from .run import execute_run

VERSION = "0.1.0"


def build_parser():
    parser = argparse.ArgumentParser(prog="benchctl")
    parser.add_argument("--version", action="store_true")
    sub = parser.add_subparsers(dest="command")
    run = sub.add_parser("run")
    run.add_argument("--config", required=True)
    run.add_argument("--preset", choices=["speed", "quality", "full-editorial"], required=True)
    run.add_argument("--provider")
    run.add_argument("--model")
    report = sub.add_parser("report")
    report.add_argument("--run", required=True)
    publish = sub.add_parser("publish-pack")
    publish.add_argument("--run", required=True)
    publish.add_argument("--destination", required=True)
    publish.add_argument("--dry-run", action="store_true")
    publish.add_argument("--approval")
    gallery = sub.add_parser("gallery-export")
    gallery.add_argument("--pack", required=True)
    gallery.add_argument("--gallery", required=True)
    gallery.add_argument("--slug", required=True)
    gallery.add_argument("--dry-run", action="store_true")
    gallery.add_argument("--approval")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.version:
        print(f"fjson-local-model-benchmark {VERSION}")
        return 0
    if args.command == "run":
        receipt = execute_run(args.config, args.preset, args.provider, args.model)
        print(json.dumps(receipt, sort_keys=True))
        return 0 if receipt["status"] == "PASS" else 1
    if args.command == "report":
        run = Path(args.run)
        print(generate_report(run / "results.json", run / "report"))
        return 0
    if args.command == "publish-pack":
        approval = json.loads(Path(args.approval).read_text()) if args.approval else None
        receipt = build_public_pack(Path(args.run), Path(args.destination), args.dry_run, approval)
        print(json.dumps(receipt, sort_keys=True))
        return 0
    if args.command == "gallery-export":
        approval = json.loads(Path(args.approval).read_text()) if args.approval else None
        receipt = export_pack(Path(args.pack), Path(args.gallery), args.slug, args.dry_run, approval=approval)
        print(json.dumps(receipt, sort_keys=True))
        return 0
    build_parser().print_help()
    return 0


def entrypoint():
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Serve the eBay report dashboard and provide a delete API for report files.

Usage:
  python scripts/report_dashboard_server.py
  python scripts/report_dashboard_server.py --port 8765 --root .
"""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve dashboard files with /api/reports delete support.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Bind port (default: 8765)")
    parser.add_argument(
        "--root",
        default=str(pathlib.Path(__file__).resolve().parents[1]),
        help="Web root directory (default: ebay-arbitrage-plugin)",
    )
    parser.add_argument(
        "--reports-dir",
        default="reports",
        help="Reports directory relative to --root (default: reports)",
    )
    return parser.parse_args()


def is_subpath(base: pathlib.Path, target: pathlib.Path) -> bool:
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False


def make_handler(root_dir: pathlib.Path, reports_dir: pathlib.Path):
    class ReportHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root_dir), **kwargs)

        def _send_json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _handle_list(self) -> None:
            files = []
            for path in sorted(reports_dir.glob("*")):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in {".md", ".html"}:
                    continue
                rel = path.relative_to(root_dir).as_posix()
                files.append(
                    {
                        "path": rel,
                        "name": path.name,
                        "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="minutes"),
                    }
                )
            self._send_json(200, {"reports": files})

        def _handle_delete(self, query: dict[str, list[str]]) -> None:
            report_path = (query.get("path") or [None])[0]
            if not report_path:
                self._send_json(400, {"error": "missing query parameter: path"})
                return

            target = (root_dir / report_path).resolve()
            if not is_subpath(reports_dir, target):
                self._send_json(400, {"error": "path must be inside reports directory"})
                return
            if not target.exists() or not target.is_file():
                self._send_json(404, {"error": "report file not found"})
                return
            if target.suffix.lower() not in {".md", ".html"}:
                self._send_json(400, {"error": "only .md and .html files can be deleted"})
                return

            target.unlink()
            self._send_json(200, {"deleted": report_path})

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/api/reports":
                self._handle_list()
                return
            super().do_GET()

        def do_DELETE(self):
            parsed = urlparse(self.path)
            if parsed.path != "/api/reports":
                self._send_json(404, {"error": "endpoint not found"})
                return
            self._handle_delete(parse_qs(parsed.query))

    return ReportHandler


def main() -> int:
    args = parse_args()
    root_dir = pathlib.Path(args.root).resolve()
    reports_dir = (root_dir / args.reports_dir).resolve()

    if not root_dir.is_dir():
        print(f"missing root directory: {root_dir}")
        return 1
    if not reports_dir.is_dir():
        print(f"missing reports directory: {reports_dir}")
        return 1

    handler = make_handler(root_dir, reports_dir)
    server = ThreadingHTTPServer((args.host, args.port), handler)

    print(f"serving {root_dir} on http://{args.host}:{args.port}")
    print("delete API: DELETE /api/reports?path=reports/<file>.md")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

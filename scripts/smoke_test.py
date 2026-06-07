from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import fitz
import requests


def _create_sample_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Day la tai lieu smoke test cho he thong RAG local.\n"
        "Noi dung chinh: upload PDF, index tai lieu va hoi dap co nguon.\n"
        "Tu khoa kiem thu: hoa sen xanh.",
        fontsize=12,
    )
    doc.save(path)
    doc.close()


def run_smoke(base_url: str) -> dict:
    """Run a minimal API smoke test against a running backend."""
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "sample-smoke-test.pdf"
        _create_sample_pdf(pdf_path)

        with pdf_path.open("rb") as handle:
            upload = requests.post(
                f"{base_url}/documents/upload",
                files={"file": (pdf_path.name, handle, "application/pdf")},
                timeout=120,
            )
        upload.raise_for_status()

        index = requests.post(
            f"{base_url}/documents/index",
            json={"file_name": pdf_path.name},
            timeout=300,
        )
        index.raise_for_status()

        search = requests.post(
            f"{base_url}/search",
            json={"question": "Tai lieu noi ve tu khoa kiem thu nao?"},
            timeout=300,
        )
        search.raise_for_status()

        return {
            "upload": upload.json(),
            "index": index.json(),
            "search_top": search.json()["results"][0] if search.json()["results"] else None,
        }


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()
    print(json.dumps(run_smoke(args.base_url.rstrip("/")), ensure_ascii=False, indent=2))

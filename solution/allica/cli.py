"""Command-line interface for the Allica pipeline.

Examples
--------
Run the pipeline against the bundled sample data and pretty-print results::

    python -m allica.cli run

Run against a custom file and write JSON to disk::

    python -m allica.cli run --input my_leads.json --output out.json

Disable email drafting (useful for fast triage previews)::

    python -m allica.cli run --no-email

Run the eval suite (cases.json) and print a green/red summary::

    python -m allica.cli eval
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core.logging_setup import configure_logging
from .core.paths import DEFAULT_LEADS_PATH
from .core.pipeline import run_pipeline


def _cmd_run(args: argparse.Namespace) -> int:
    leads_path = Path(args.input) if args.input else DEFAULT_LEADS_PATH
    leads = json.loads(leads_path.read_text(encoding="utf-8"))
    response = run_pipeline(
        leads, draft_email=not args.no_email, prefer_llm=args.llm
    )
    payload = response.model_dump(mode="json")
    text = json.dumps(payload, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(text)

    if args.summary:
        s = response.summary
        print(
            "\n— Summary —\n"
            f"  received   : {s.received}\n"
            f"  processed  : {s.processed}\n"
            f"  duplicates : {s.duplicates}\n"
            f"  by_owner   : {s.by_owner}\n"
            f"  by_band    : {s.by_band}\n"
            f"  elapsed_ms : {s.elapsed_ms}\n",
            file=sys.stderr,
        )
    return 0


def _cmd_eval(args: argparse.Namespace) -> int:
    from .tests.eval_runner import run_eval

    results = run_eval(verbose=args.verbose)
    failed = [r for r in results if not r["passed"]]
    print(f"\n{len(results) - len(failed)}/{len(results)} eval cases passed.")
    return 0 if not failed else 1


def main(argv: list[str] | None = None) -> int:
    configure_logging("WARNING")  # CLI prints data; quiet logs by default.
    parser = argparse.ArgumentParser(prog="allica", description="Allica GTM Assistant CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Run the pipeline.")
    run_p.add_argument("-i", "--input", help="Path to a leads JSON file.")
    run_p.add_argument("-o", "--output", help="Where to write the JSON response.")
    run_p.add_argument("--no-email", action="store_true", help="Skip email drafting.")
    run_p.add_argument("--llm", action="store_true", help="Prefer LLM email drafting.")
    run_p.add_argument("--summary", action="store_true", help="Print a short summary to stderr.")
    run_p.set_defaults(func=_cmd_run)

    eval_p = sub.add_parser("eval", help="Run the evals/cases.json suite.")
    eval_p.add_argument("-v", "--verbose", action="store_true")
    eval_p.set_defaults(func=_cmd_eval)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

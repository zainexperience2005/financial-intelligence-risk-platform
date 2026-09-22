"""Admin CLI script to inspect recent audit events.

Usage:
    python scripts/show_audit_events.py [--limit 20]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure src/ is on sys.path for direct CLI execution
src_path = str(Path(__file__).resolve().parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


def main(argv: list[str] | None = None) -> int:
    from app.db.repositories.audit import find_recent_audit_events
    from kit.databases.session import SessionFactory

    parser = argparse.ArgumentParser(
        description="Inspect authoritative audit events from PostgreSQL."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of audit events to display (default: 20)",
    )
    parser.add_argument(
        "--event-type",
        type=str,
        default=None,
        help="Filter by specific event_type (e.g. action_execution_denied)",
    )
    args = parser.parse_args(argv)

    with SessionFactory() as session:
        events = find_recent_audit_events(
            session=session,
            limit=args.limit,
            event_type=args.event_type,
        )

        if not events:
            print(
                f"No audit events found"
                f"{f' for event_type={args.event_type}' if args.event_type else ''}."
            )
            return 0

        print(
            f"Found {len(events)} audit event(s)"
            f"{f' matching {args.event_type}' if args.event_type else ''}:"
        )
        print("-" * 88)
        for ev in events:
            details_str = json.dumps(ev.details, default=str)
            print(
                f"[{ev.created_at.isoformat()}] ID={ev.id} | "
                f"EVENT={ev.event_type} | "
                f"ACTOR={ev.actor} | "
                f"ENTITY={ev.entity_type}:{ev.entity_id}"
            )
            print(f"  DETAILS: {details_str}")
            print("-" * 88)

    return 0


if __name__ == "__main__":
    sys.exit(main())

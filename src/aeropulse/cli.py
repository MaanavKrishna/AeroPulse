"""Command line: `aeropulse <command>`. Run `aeropulse --help` for the list."""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys

from .config import get_settings


def _date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def cmd_db(args) -> int:
    from .db.session import init_db
    if args.action == "init":
        init_db()
        print("Tables created.")
    else:
        from .db.migrate import upgrade
        upgrade()
        print("Database is at the latest migration.")
    return 0


def cmd_collect(args) -> int:
    from .db.session import init_db, session_scope
    from .pipeline.collect import collect, today_ist
    from .providers import make_provider
    from .reference import routes_to_collect

    settings = get_settings()
    settings.check()
    init_db()
    day = args.date or today_ist()
    names = [args.provider] if args.provider else settings.provider_list
    routes = routes_to_collect(day)
    if args.limit:
        routes = routes[: args.limit]
    worst = 0
    for name in names:
        provider = make_provider(name, settings, day)
        try:
            with session_scope() as s:
                run = collect(s, provider, routes, day,
                              max_calls_per_day=settings.max_calls_per_day)
                print(f"{name}: {run.status}. {run.routes_ok}/{run.routes_requested} routes, "
                      f"{run.fares_stored} fares, {run.calls} calls.")
                if run.message:
                    print(run.message)
                worst = max(worst, 0 if run.status == "ok" else 1)
        finally:
            provider.close()
    return worst


def cmd_build(args) -> int:
    from .db.session import init_db, session_scope
    from .pipeline.build import build
    from .reference import load_basket

    settings = get_settings()
    init_db()
    provider = args.provider or settings.provider_list[0]
    with session_scope() as s:
        r = build(s, load_basket(), provider, reason=args.reason,
                  replications=args.replications)
    print(f"Built from {r.provider}: {r.days} days, {r.product_days} product-days, "
          f"{r.points_written} points, {r.revisions} revisions, {r.links} links"
          f"{' (DEMO DATA)' if r.is_demo else ''}.")
    return 0


def cmd_demo(args) -> int:
    """Fill a development database with labelled synthetic history, then build."""
    from .db.session import init_db, session_scope
    from .pipeline.build import build
    from .pipeline.collect import collect, purge_day, today_ist
    from .providers.demo import DemoProvider
    from .reference import load_basket, routes_to_collect

    settings = get_settings()
    if settings.is_production:
        print("Refusing to write demo data with AEROPULSE_ENV=production.", file=sys.stderr)
        return 2
    init_db()
    end = args.end or today_ist()
    versions = load_basket()
    # Demo history starts before the basket's real start date, so pretend the first
    # version began on the first demo day.
    first = end - dt.timedelta(days=args.days - 1)
    from .reference import BasketVersion
    demo_versions = [BasketVersion(v.version, min(v.valid_from, first) if i == 0
                                   else v.valid_from, v.routes)
                     for i, v in enumerate(versions)]
    for i in range(args.days):
        day = first + dt.timedelta(days=i)
        with session_scope() as s:
            purge_day(s, "demo", day)
            collect(s, DemoProvider(day), routes_to_collect(day, demo_versions), day,
                    max_calls_per_day=10_000)
        if (i + 1) % 30 == 0 or i + 1 == args.days:
            print(f"  collected {i + 1}/{args.days} demo days")
    with session_scope() as s:
        r = build(s, demo_versions, "demo", reason="demo build",
                  replications=args.replications)
    print(f"Demo database ready: {r.days} days, {r.points_written} points. "
          "Everything in it is synthetic and labelled as such.")
    return 0


def cmd_export(args) -> int:
    from .db.session import session_scope
    from .pipeline.export import export
    with session_scope() as s:
        manifest = export(s, args.out or get_settings().export_dir)
    print(f"Exported {len(manifest['files'])} files to {manifest['directory']}.")
    return 0


def cmd_rebuild(args) -> int:
    from .pipeline.rebuild import compare
    checked, bad = compare(args.directory)
    if bad:
        print(f"{len(bad)} of {checked} national points do not match:")
        print("\n".join(bad[:20]))
        return 1
    print(f"All {checked} national index points rebuilt exactly from the published files.")
    return 0


def cmd_dgca(args) -> int:
    from .db.session import init_db, session_scope
    from .official.dgca import import_csv
    init_db()
    with session_scope() as s:
        n = import_csv(s, args.file)
    print(f"Imported {n} DGCA traffic rows. Run `aeropulse build` to apply the weights.")
    return 0


def cmd_cpi(args) -> int:
    from .db.session import init_db, session_scope
    from .official.mospi_cpi import import_csv
    init_db()
    with session_scope() as s:
        n = import_csv(s, args.file)
    print(f"Imported {n} CPI airfare rows.")
    return 0


def cmd_serve(args) -> int:
    import uvicorn
    get_settings().check()
    uvicorn.run("aeropulse.app:app", host=args.host, port=args.port, reload=args.reload)
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(prog="aeropulse", description="Open Indian airfare index.")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("db", help="create or migrate the database")
    s.add_argument("action", choices=["init", "upgrade"])
    s.set_defaults(func=cmd_db)

    s = sub.add_parser("collect", help="collect today's fares from the configured providers")
    s.add_argument("--provider")
    s.add_argument("--limit", type=int, help="only the first N basket routes (for trials)")
    s.add_argument("--date", type=_date, help="collection date (default: today in IST)")
    s.set_defaults(func=cmd_collect)

    s = sub.add_parser("build", help="rebuild all published series from stored fares")
    s.add_argument("--provider")
    s.add_argument("--replications", type=int, default=200)
    s.add_argument("--reason", default="scheduled rebuild")
    s.set_defaults(func=cmd_build)

    s = sub.add_parser("demo", help="fill a development database with synthetic history")
    s.add_argument("--days", type=int, default=150)
    s.add_argument("--end", type=_date)
    s.add_argument("--replications", type=int, default=100)
    s.set_defaults(func=cmd_demo)

    s = sub.add_parser("export", help="write the open dataset (CSV + checksums)")
    s.add_argument("--out")
    s.set_defaults(func=cmd_export)

    s = sub.add_parser("rebuild", help="recompute the national index from an export and "
                                       "check it matches what was published")
    s.add_argument("directory")
    s.set_defaults(func=cmd_rebuild)

    s = sub.add_parser("dgca-import", help="import DGCA city-pair traffic from CSV")
    s.add_argument("file")
    s.set_defaults(func=cmd_dgca)

    s = sub.add_parser("cpi-import", help="import the MoSPI CPI airfare series from CSV")
    s.add_argument("file")
    s.set_defaults(func=cmd_cpi)

    s = sub.add_parser("serve", help="run the website and API")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    s.add_argument("--reload", action="store_true")
    s.set_defaults(func=cmd_serve)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

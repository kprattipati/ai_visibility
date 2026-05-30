from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from ai_visibility.data import PRACTICE_AREAS, TOP_CITIES, get_city, get_practice_area
from ai_visibility.engines import MockEngineClient, build_engine_client
from ai_visibility.geo import CITY_GEO, scopes_for
from ai_visibility.models import EngineAnswer
from ai_visibility.prompts import generate_prompts
from ai_visibility.reports import build_markdown_report
from ai_visibility.scoring import score_answers
from ai_visibility.seeds import sample_businesses
from ai_visibility.storage import VisibilityStore


def main() -> None:
    parser = argparse.ArgumentParser(prog="ai-visibility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-markets", help="Show seeded cities and practice areas.")

    db_parser = subparsers.add_parser("init-db", help="Create or update the local SQLite database.")
    db_parser.add_argument("--db", default="data/visibility.db")

    prompt_parser = subparsers.add_parser("generate-prompts", help="Generate buyer prompts.")
    prompt_parser.add_argument("--city", required=True)
    prompt_parser.add_argument("--practice-area", required=True)
    prompt_parser.add_argument("--limit", type=int)
    add_geo_arguments(prompt_parser)

    audit_parser = subparsers.add_parser("run-audit", help="Run a mock visibility audit.")
    audit_parser.add_argument("--city", required=True)
    audit_parser.add_argument("--practice-area", required=True)
    audit_parser.add_argument("--business", required=True)
    audit_parser.add_argument("--limit", type=int, default=24)
    audit_parser.add_argument("--out", required=True)
    audit_parser.add_argument("--db", default="data/visibility.db")
    audit_parser.add_argument("--use-cache", action="store_true")
    audit_parser.add_argument("--force-refresh", action="store_true")
    audit_parser.add_argument("--engine", default=None)
    audit_parser.add_argument("--config", default="config/providers.json")
    add_geo_arguments(audit_parser)

    monthly_parser = subparsers.add_parser("monthly-index", help="Build a cached monthly market index.")
    monthly_parser.add_argument("--db", default="data/visibility.db")
    monthly_parser.add_argument("--city", required=True)
    monthly_parser.add_argument("--practice-area", required=True)
    monthly_parser.add_argument("--business", default="Example Injury Law")
    monthly_parser.add_argument("--limit", type=int, default=75)
    monthly_parser.add_argument("--out")
    monthly_parser.add_argument("--force-refresh", action="store_true")
    monthly_parser.add_argument("--engine", default=None)
    monthly_parser.add_argument("--config", default="config/providers.json")
    add_geo_arguments(monthly_parser, default_scope="sample")

    batch_parser = subparsers.add_parser(
        "batch-snapshot",
        help="Generate a cold-email snapshot report for every seeded firm in a market (shares cached answers).",
    )
    batch_parser.add_argument("--db", default="data/visibility.db")
    batch_parser.add_argument("--city", required=True)
    batch_parser.add_argument("--practice-area", required=True)
    batch_parser.add_argument("--limit", type=int, default=12, help="Prompts per snapshot (10-15 for cold email).")
    batch_parser.add_argument("--out-dir", default="reports/batch")
    batch_parser.add_argument("--force-refresh", action="store_true")
    batch_parser.add_argument("--engine", default=None)
    batch_parser.add_argument("--config", default="config/providers.json")
    add_geo_arguments(batch_parser)

    check_parser = subparsers.add_parser("customer-check", help="Run a smaller cached customer visibility check.")
    check_parser.add_argument("--db", default="data/visibility.db")
    check_parser.add_argument("--city", required=True)
    check_parser.add_argument("--practice-area", required=True)
    check_parser.add_argument("--business", required=True)
    check_parser.add_argument("--limit", type=int, default=24)
    check_parser.add_argument("--out")
    check_parser.add_argument("--force-refresh", action="store_true")
    check_parser.add_argument("--engine", default=None)
    check_parser.add_argument("--config", default="config/providers.json")
    add_geo_arguments(check_parser)

    args = parser.parse_args()

    try:
        if args.command == "list-markets":
            list_markets()
        elif args.command == "init-db":
            init_db(args)
        elif args.command == "generate-prompts":
            city = get_city(args.city)
            area = get_practice_area(args.practice_area)
            geo_scopes = scopes_for(city, args.geo_scope, args.neighborhood, args.zip_code)
            for prompt in generate_prompts(city, area, args.limit, geo_scopes):
                print(prompt)
        elif args.command == "run-audit":
            run_audit(args)
        elif args.command == "monthly-index":
            run_stored_audit(args, run_type="monthly-index", default_use_cache=True)
        elif args.command == "batch-snapshot":
            run_batch_snapshot(args)
        elif args.command == "customer-check":
            run_stored_audit(args, run_type="customer-check", default_use_cache=True)
    except (ValueError, NotImplementedError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def list_markets() -> None:
    print("Cities")
    for city in TOP_CITIES:
        print(f"- {city.name}, {city.state} ({city.population_2025:,})")
    print("\nPractice areas")
    for area in PRACTICE_AREAS:
        print(f"- {area.slug}: {area.label}")


def add_geo_arguments(parser: argparse.ArgumentParser, default_scope: str = CITY_GEO) -> None:
    parser.add_argument(
        "--geo-scope",
        default=default_scope,
        choices=("city", "sample", "neighborhood", "zip"),
        help="Geographic prompt scope.",
    )
    parser.add_argument(
        "--neighborhood",
        action="append",
        help="Neighborhood to target. Can be provided multiple times.",
    )
    parser.add_argument(
        "--zip-code",
        action="append",
        help="ZIP code to target. Can be provided multiple times.",
    )


def run_audit(args: argparse.Namespace) -> None:
    city = get_city(args.city)
    area = get_practice_area(args.practice_area)
    geo_scopes = scopes_for(city, args.geo_scope, args.neighborhood, args.zip_code)
    prompts = generate_prompts(city, area, args.limit, geo_scopes)
    businesses = sample_businesses(city.name, area.slug, args.business)
    if args.use_cache or args.force_refresh:
        answers, scores = _run_with_storage(
            db_path=args.db,
            run_type="ad-hoc-audit",
            city=city,
            area=area,
            target_business=args.business,
            prompts=prompts,
            businesses=businesses,
            force_refresh=args.force_refresh,
            engine_name=args.engine,
            config_path=args.config,
        )
    else:
        engine = build_engine_client(args.engine, args.config)
        answers = [engine.ask(prompt, businesses) for prompt in prompts]
        scores = score_answers(businesses, answers)
    report = build_markdown_report(city, area, args.business, answers, scores)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path}")


def init_db(args: argparse.Namespace) -> None:
    store = VisibilityStore(args.db)
    try:
        store.init_schema()
    finally:
        store.close()
    print(f"Initialized {args.db}")


def run_stored_audit(args: argparse.Namespace, run_type: str, default_use_cache: bool) -> None:
    city = get_city(args.city)
    area = get_practice_area(args.practice_area)
    geo_scopes = scopes_for(city, args.geo_scope, args.neighborhood, args.zip_code)
    prompts = generate_prompts(city, area, args.limit, geo_scopes)
    businesses = sample_businesses(city.name, area.slug, args.business)
    answers, scores = _run_with_storage(
        db_path=args.db,
        run_type=run_type,
        city=city,
        area=area,
        target_business=args.business,
        prompts=prompts,
        businesses=businesses,
        force_refresh=args.force_refresh,
        engine_name=args.engine,
        config_path=args.config,
    )
    if args.out:
        out_path = Path(args.out)
    else:
        filename = f"{city.name.lower().replace(' ', '-')}-{area.slug.replace(' ', '-')}-{run_type}.md"
        out_path = Path("reports") / filename
    report = build_markdown_report(city, area, args.business, answers, scores)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path}")


def run_batch_snapshot(args: argparse.Namespace) -> None:
    city = get_city(args.city)
    area = get_practice_area(args.practice_area)
    geo_scopes = scopes_for(city, args.geo_scope, args.neighborhood, args.zip_code)
    prompts = generate_prompts(city, area, args.limit, geo_scopes)

    # Use a placeholder target to load the full seeded competitor list.
    all_businesses = sample_businesses(city.name, area.slug, "__batch__")
    # Drop the synthetic placeholder we inserted (not a real firm).
    businesses = [b for b in all_businesses if b.name != "__batch__"]

    if not businesses:
        raise ValueError(f"No seeded competitors found for {city.name} / {area.slug}.")

    # Run prompts once against the full competitor set and cache results.
    store = VisibilityStore(args.db)
    engine = build_engine_client(args.engine, args.config)
    candidate_signature = _candidate_signature(businesses)
    try:
        store.init_schema()
        market_id = store.get_or_create_market(city, area)
        store.upsert_businesses(market_id, businesses)
        prompt_ids = store.upsert_prompts(market_id, prompts)

        answers: list[EngineAnswer] = []
        cache_hits = 0
        fresh_runs = 0
        for prompt in prompts:
            prompt_id = prompt_ids[prompt]
            answer = None if args.force_refresh else store.cached_answer(
                prompt_id, engine.name, candidate_signature
            )
            if answer is None:
                answer = engine.ask(prompt, businesses)
                store.save_answer(market_id, prompt_id, answer, candidate_signature)
                fresh_runs += 1
            else:
                cache_hits += 1
            answers.append(answer)
        print(f"{cache_hits} cached answers, {fresh_runs} fresh answers for {len(prompts)} prompts.")

        scores = score_answers(businesses, answers)
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = f"{city.name.lower().replace(' ', '-')}-{area.slug.replace(' ', '-')}"

        for business in businesses:
            report = build_markdown_report(city, area, business.name, answers, scores)
            filename = business.name.lower().replace(" ", "-").replace(",", "").replace(".", "") + f"-{slug}.md"
            out_path = out_dir / filename
            out_path.write_text(report, encoding="utf-8")
            target_score = next(s for s in scores if s.business.name == business.name)
            rank = scores.index(target_score) + 1
            print(f"  [{rank}/{len(businesses)}] {business.name} → {out_path}")
    finally:
        store.close()


def _run_with_storage(
    db_path: str,
    run_type: str,
    city,
    area,
    target_business: str,
    prompts: list[str],
    businesses,
    force_refresh: bool,
    engine_name: str | None = None,
    config_path: str | None = None,
) -> tuple[list[EngineAnswer], list]:
    store = VisibilityStore(db_path)
    engine = build_engine_client(engine_name, config_path)
    candidate_signature = _candidate_signature(businesses)
    try:
        store.init_schema()
        market_id = store.get_or_create_market(city, area)
        business_ids = store.upsert_businesses(market_id, businesses)
        prompt_ids = store.upsert_prompts(market_id, prompts)

        answers: list[EngineAnswer] = []
        cache_hits = 0
        fresh_runs = 0
        for prompt in prompts:
            prompt_id = prompt_ids[prompt]
            answer = None if force_refresh else store.cached_answer(
                prompt_id,
                engine.name,
                candidate_signature,
            )
            if answer is None:
                answer = engine.ask(prompt, businesses)
                store.save_answer(market_id, prompt_id, answer, candidate_signature)
                fresh_runs += 1
            else:
                cache_hits += 1
            answers.append(answer)

        scores = score_answers(businesses, answers)
        run = store.create_run(
            run_type=run_type,
            market_id=market_id,
            target_business_id=business_ids[target_business],
            engine=engine.name,
            prompt_count=len(prompts),
        )
        store.save_scores(run.id, business_ids, scores, len(prompts))
        print(
            f"Stored run {run.id}: {cache_hits} cached answers, {fresh_runs} fresh answers, {store.answer_count()} total saved answers"
        )
        return answers, scores
    finally:
        store.close()


def _candidate_signature(businesses) -> str:
    values = sorted(
        f"{business.name}|{business.website or ''}|{','.join(business.aliases)}"
        for business in businesses
    )
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    main()

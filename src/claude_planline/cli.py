from __future__ import annotations

import argparse
import json
import math
import os
import re
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BAR_WIDTH = 10


@dataclass
class WindowUsage:
    used_percent: float | None = None
    resets_at: Any = None


@dataclass
class CreditUsage:
    used_percent: float | None = None
    spent: float | None = None
    limit: float | None = None
    currency: str | None = None
    resets_at: Any = None
    active: bool | None = None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="claude-planline",
        description="Tiny Claude Code statusLine helper.",
    )
    add_shared_options(parser, with_defaults=True)

    subparsers = parser.add_subparsers(dest="action")
    preview_parser = subparsers.add_parser("preview", help="Show sample output.")
    add_shared_options(preview_parser, with_defaults=False)

    dump_parser = subparsers.add_parser("dump", help="Write stdin JSON to ~/.claude/last-statusline-input.json.")
    add_shared_options(dump_parser, with_defaults=False)

    install_parser = subparsers.add_parser("install", help="Install into ~/.claude/settings.json.")
    add_shared_options(install_parser, with_defaults=False)
    install_parser.add_argument("--dry-run", action="store_true")
    install_parser.add_argument("--command", dest="status_command", default=None, help="Command to write into settings.json.")
    install_parser.add_argument(
        "--preserve-existing",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Wrap the existing statusLine instead of replacing it.",
    )
    install_parser.add_argument(
        "--layout",
        choices=["two-line", "inline"],
        default="two-line",
        help="How to combine an existing statusLine with claude-planline.",
    )
    install_parser.add_argument("--refresh-interval", type=int, default=60)

    uninstall_parser = subparsers.add_parser("uninstall", help="Remove statusLine from ~/.claude/settings.json.")
    add_shared_options(uninstall_parser, with_defaults=False)

    args = parser.parse_args(argv)
    color = not args.no_color and os.getenv("NO_COLOR") is None

    if args.action == "preview":
        print_preview(args.lang, args.style, color)
        return 0

    if args.action == "install":
        return install(args)

    if args.action == "uninstall":
        return uninstall()

    raw = sys.stdin.read()

    if args.action == "dump":
        return dump(raw)

    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    print(render(payload, lang=args.lang, style=args.style, color=color))
    return 0


def add_shared_options(parser: argparse.ArgumentParser, *, with_defaults: bool) -> None:
    default_style = os.getenv("CLAUDE_PLANLINE_STYLE", "cute") if with_defaults else argparse.SUPPRESS
    default_lang = os.getenv("CLAUDE_PLANLINE_LANG", "es") if with_defaults else argparse.SUPPRESS
    default_no_color = False if with_defaults else argparse.SUPPRESS

    parser.add_argument("--style", choices=["cute", "plain"], default=default_style)
    parser.add_argument("--lang", choices=["es", "en"], default=default_lang)
    parser.add_argument("--no-color", action="store_true", default=default_no_color, help="Disable ANSI colors.")


def render(payload: dict[str, Any], *, lang: str = "es", style: str = "cute", color: bool = True) -> str:
    five_hour = extract_window(payload)
    credits = extract_credits(payload)

    parts: list[str] = []

    if five_hour.used_percent is not None:
        parts.append(render_five_hour(five_hour, lang=lang, style=style, color=color))

    if credits.used_percent is not None or credits.spent is not None or credits.limit is not None:
        parts.append(render_credits(credits, lang=lang, style=style, color=color))

    if parts:
        return " | ".join(parts)

    return "(-_-) sin datos" if lang == "es" else "(-_-) no data"


def extract_window(payload: dict[str, Any]) -> WindowUsage:
    rate_limits = first_dict(payload, ["rate_limits", "rateLimits", "limits"])
    candidates = [
        first_dict(rate_limits, ["five_hour", "fiveHour", "5h", "current_session", "currentSession"]),
        first_dict(payload, ["five_hour", "fiveHour", "current_session", "currentSession"]),
    ]

    for candidate in candidates:
        if not candidate:
            continue
        percent = first_number(candidate, ["used_percentage", "usedPercent", "percentage", "percent", "used"])
        reset = first_value(candidate, ["resets_at", "resetsAt", "reset_at", "resetAt", "reset", "resets"])
        if percent is not None or reset is not None:
            return WindowUsage(used_percent=normalize_percent(percent), resets_at=reset)

    return WindowUsage()


def extract_credits(payload: dict[str, Any]) -> CreditUsage:
    candidates = [
        first_dict(payload, ["usage_credits", "usageCredits", "credits", "credit_usage", "creditUsage"]),
        first_dict(payload, ["extra_usage", "extraUsage", "overage", "billing"]),
    ]

    for candidate in candidates:
        if not candidate:
            continue

        spent, limit, currency = extract_money_pair(candidate)
        percent = first_number(
            candidate,
            ["used_percentage", "usedPercent", "percentage", "percent", "used_percent", "usedPercent"],
        )
        if percent is None and spent is not None and limit:
            percent = (spent / limit) * 100

        reset = first_value(candidate, ["resets_at", "resetsAt", "reset_at", "resetAt", "reset", "resets"])
        active = first_bool(candidate, ["active", "enabled", "is_active", "isActive"])

        if percent is not None or spent is not None or limit is not None:
            return CreditUsage(
                used_percent=normalize_percent(percent),
                spent=spent,
                limit=limit,
                currency=currency,
                resets_at=reset,
                active=active,
            )

    return CreditUsage()


def render_five_hour(usage: WindowUsage, *, lang: str, style: str, color: bool) -> str:
    used = clamp(usage.used_percent or 0, 0, 100)
    remaining = max(0, 100 - used)
    face = face_for_percent(used, style=style)
    bar = render_bar(used, color=color)
    reset = format_reset(usage.resets_at, lang=lang)

    if lang == "en":
        text = f"{face} 5h {bar} {used:.0f}% used · left {remaining:.0f}%"
    else:
        text = f"{face} 5h {bar} {used:.0f}% usado · queda {remaining:.0f}%"

    if reset:
        text += f" · reset {reset}"
    return text


def render_credits(credits: CreditUsage, *, lang: str, style: str, color: bool) -> str:
    used = credits.used_percent
    if used is None and credits.spent is not None and credits.limit:
        used = (credits.spent / credits.limit) * 100
    used = clamp(used or 0, 0, 100)

    face = money_face_for_percent(used, style=style)
    bar = render_bar(used, color=color, money=True)
    reset = format_reset(credits.resets_at, lang=lang)
    amount = format_money(credits.spent, credits.limit, credits.currency, lang=lang)

    label = "extra" if lang == "en" else "extra"
    text = f"{face} {label} {bar}"
    if amount:
        text += f" {amount}"
    else:
        text += f" {used:.0f}%"
    if reset:
        text += f" · reset {reset}"
    return text


def render_bar(percent: float, *, color: bool, money: bool = False) -> str:
    filled = int(round((clamp(percent, 0, 100) / 100) * BAR_WIDTH))
    bar = "█" * filled + "░" * (BAR_WIDTH - filled)
    if not color:
        return f"[{bar}]"

    if percent >= 90:
        code = "31"
    elif percent >= 70:
        code = "33"
    elif money:
        code = "36"
    else:
        code = "32"
    return f"\033[{code}m[{bar}]\033[0m"


def face_for_percent(percent: float, *, style: str) -> str:
    if style == "plain":
        return "Claude"
    if percent >= 90:
        return "(×_×)"
    if percent >= 80:
        return "(•_•)"
    if percent >= 60:
        return "(•_•)"
    return "(•‿•)"


def money_face_for_percent(percent: float, *, style: str) -> str:
    if style == "plain":
        return "$"
    if percent >= 90:
        return "($×$)"
    return "($‿$)"


def format_reset(value: Any, *, lang: str) -> str:
    if value is None:
        return ""

    if isinstance(value, (int, float)):
        # Accept seconds or milliseconds.
        ts = value / 1000 if value > 10_000_000_000 else value
        try:
            dt = datetime.fromtimestamp(ts, timezone.utc).astimezone()
            return dt.strftime("%H:%M")
        except (OverflowError, OSError, ValueError):
            return str(value)

    text = str(value).strip()
    if not text:
        return ""

    parsed = parse_iso_datetime(text)
    if parsed:
        return parsed.astimezone().strftime("%H:%M")

    return text


def parse_iso_datetime(text: str) -> datetime | None:
    try:
        normalized = text.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def extract_money_pair(candidate: dict[str, Any]) -> tuple[float | None, float | None, str | None]:
    spent = first_number(
        candidate,
        ["spent", "spent_amount", "spentAmount", "used_amount", "usedAmount", "used", "cost", "amount"],
    )
    limit = first_number(
        candidate,
        ["limit", "monthly_limit", "monthlyLimit", "budget", "cap", "max", "credit_limit", "creditLimit"],
    )
    currency = first_string(candidate, ["currency", "currency_symbol", "currencySymbol", "symbol"])

    # Fallback for strings like "€25.14 / €30.00 spent".
    for value in candidate.values():
        if isinstance(value, str):
            parsed = parse_money_text(value)
            if parsed:
                p_spent, p_limit, p_currency = parsed
                spent = spent if spent is not None else p_spent
                limit = limit if limit is not None else p_limit
                currency = currency or p_currency

    return spent, limit, currency


def parse_money_text(text: str) -> tuple[float | None, float | None, str | None] | None:
    match = re.search(r"([€$£])\s*([0-9]+(?:[.,][0-9]+)?)\s*/\s*([€$£])?\s*([0-9]+(?:[.,][0-9]+)?)", text)
    if not match:
        return None
    currency = match.group(1)
    spent = parse_float(match.group(2))
    limit = parse_float(match.group(4))
    return spent, limit, currency


def format_money(spent: float | None, limit: float | None, currency: str | None, *, lang: str) -> str:
    if spent is None and limit is None:
        return ""
    symbol = currency_symbol(currency)
    period = "month" if lang == "en" else "mes"
    if spent is not None and limit is not None:
        return f"{symbol}{spent:.2f}/{symbol}{trim_money(limit)} {period}"
    if spent is not None:
        return f"{symbol}{spent:.2f} {period}"
    return f"/{symbol}{trim_money(limit)} {period}"


def currency_symbol(currency: str | None) -> str:
    if not currency:
        return "€"
    mapping = {"EUR": "€", "USD": "$", "GBP": "£"}
    return mapping.get(currency.upper(), currency)


def trim_money(value: float | None) -> str:
    if value is None:
        return ""
    if math.isclose(value, round(value)):
        return str(int(round(value)))
    return f"{value:.2f}"


def first_dict(data: dict[str, Any] | None, keys: list[str]) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    for key in keys:
        value = data.get(key)
        if isinstance(value, dict):
            return value
    return {}


def first_value(data: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


def first_number(data: dict[str, Any], keys: list[str]) -> float | None:
    for key in keys:
        if key in data:
            parsed = parse_float(data[key])
            if parsed is not None:
                return parsed
    return None


def first_string(data: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def first_bool(data: dict[str, Any], keys: list[str]) -> bool | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, bool):
            return value
    return None


def parse_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace("%", "").replace(",", ".")
        match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
        if match:
            return float(match.group(0))
    return None


def normalize_percent(value: float | None) -> float | None:
    if value is None:
        return None
    if 0 <= value <= 1:
        return value * 100
    return value


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def dump(raw: str) -> int:
    target = Path.home() / ".claude" / "last-statusline-input.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        payload = json.loads(raw) if raw.strip() else {}
        text = json.dumps(payload, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        text = raw
    target.write_text(text, encoding="utf-8")
    print(f"dump saved: {target}")
    return 0


def install(args: argparse.Namespace) -> int:
    settings_path = Path.home() / ".claude" / "settings.json"
    settings = read_settings(settings_path)
    existing_status = settings.get("statusLine") if isinstance(settings.get("statusLine"), dict) else None
    existing_command = existing_status.get("command") if existing_status else None
    planline_command = args.status_command or current_command(args)

    if args.preserve_existing and existing_command and "claude-planline" not in existing_command:
        wrapper_path = Path.home() / ".claude" / "claude-planline-wrapper.sh"
        command = str(wrapper_path)
        wrapper = wrapper_script(
            existing_command=existing_command,
            planline_command=planline_command,
            layout=args.layout,
        )
    else:
        wrapper_path = None
        wrapper = None
        command = planline_command

    status_line = {
        "type": "command",
        "command": command,
        "refreshInterval": args.refresh_interval,
        "padding": 1,
    }

    new_settings = dict(settings)
    new_settings["statusLine"] = status_line

    if args.dry_run:
        print(json.dumps(new_settings, indent=2, ensure_ascii=False))
        if wrapper_path and wrapper:
            print(f"\n# Wrapper that would be written to {wrapper_path}:\n{wrapper}")
        return 0

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    if settings_path.exists():
        backup = settings_path.with_suffix(f".json.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        backup.write_text(settings_path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"backup: {backup}")

    if wrapper_path and wrapper:
        wrapper_path.write_text(wrapper, encoding="utf-8")
        wrapper_path.chmod(0o755)
        print(f"wrapper: {wrapper_path}")

    settings_path.write_text(json.dumps(new_settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"installed statusLine in {settings_path}")
    return 0


def uninstall() -> int:
    settings_path = Path.home() / ".claude" / "settings.json"
    settings = read_settings(settings_path)
    if "statusLine" not in settings:
        print("statusLine not found")
        return 0

    backup = settings_path.with_suffix(f".json.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    backup.write_text(settings_path.read_text(encoding="utf-8"), encoding="utf-8")
    settings.pop("statusLine", None)
    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"removed statusLine; backup: {backup}")
    return 0


def current_command(args: argparse.Namespace) -> str:
    executable = Path(sys.argv[0])
    if executable.exists():
        command = shlex.quote(str(executable.resolve()))
    else:
        command = "claude-planline"
    return f"{command} --lang {shlex.quote(args.lang)} --style {shlex.quote(args.style)}"


def wrapper_script(*, existing_command: str, planline_command: str, layout: str) -> str:
    if layout == "inline":
        joiner = "printf '%s | %s' \"$old\" \"$plan\""
    else:
        joiner = "printf '%s\\n%s' \"$old\" \"$plan\""

    return f"""#!/usr/bin/env bash
# Generated by claude-planline. Keeps the existing statusLine and adds plan usage.
input=$(cat)
old=$(printf '%s' "$input" | {existing_command})
plan=$(printf '%s' "$input" | {planline_command})
if [ -n "$old" ] && [ -n "$plan" ]; then
  {joiner}
elif [ -n "$old" ]; then
  printf '%s' "$old"
else
  printf '%s' "$plan"
fi
"""


def read_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot parse {path}: {exc}") from exc


def print_preview(lang: str, style: str, color: bool) -> None:
    samples = [
        {"rate_limits": {"five_hour": {"used_percentage": 18, "resets_at": "2026-06-07T03:42:00Z"}}},
        {"rate_limits": {"five_hour": {"used_percentage": 61, "resets_at": "2026-06-07T01:55:00Z"}}},
        {"rate_limits": {"five_hour": {"used_percentage": 91, "resets_at": "2026-06-07T00:28:00Z"}}},
        {"usage_credits": {"used_percentage": 83, "spent": 25.14, "limit": 30, "currency": "EUR", "resets_at": "Jul 1"}},
        {},
    ]
    for sample in samples:
        print(render(sample, lang=lang, style=style, color=color))


if __name__ == "__main__":
    raise SystemExit(main())

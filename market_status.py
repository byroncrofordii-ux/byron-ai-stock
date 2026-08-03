"""U.S. stock market status helper for B.Y.R.O.N."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

EASTERN = ZoneInfo("America/New_York")


def _format_duration(delta: timedelta) -> str:
    total_minutes = max(0, int(delta.total_seconds() // 60))
    hours, minutes = divmod(total_minutes, 60)

    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def _next_weekday_open(now: datetime) -> datetime:
    candidate = now

    while True:
        candidate += timedelta(days=1)

        if candidate.weekday() < 5:
            return candidate.replace(
                hour=9,
                minute=30,
                second=0,
                microsecond=0,
            )


def get_market_status() -> dict:
    """
    Return the current U.S. stock-market session status.

    If pandas_market_calendars is installed, holidays and special
    closures are handled automatically. Otherwise, weekday trading
    hours are used as a fallback.
    """
    now = datetime.now(EASTERN)

    try:
        import pandas_market_calendars as mcal

        nyse = mcal.get_calendar("NYSE")
        schedule = nyse.schedule(
            start_date=now.date() - timedelta(days=1),
            end_date=now.date() + timedelta(days=10),
        )

        today_key = str(now.date())
        today_row = schedule.loc[today_key] if today_key in schedule.index else None

        if today_row is not None:
            market_open = today_row["market_open"].tz_convert(EASTERN).to_pydatetime()
            market_close = today_row["market_close"].tz_convert(EASTERN).to_pydatetime()

            if now < market_open:
                wait = _format_duration(market_open - now)
                return {
                    "label": "Pre-Market",
                    "emoji": "🟡",
                    "detail": f"Opens in {wait}",
                    "assistant_message": (
                        f"Coffee's brewing... Wall Street wakes up in {wait}."
                    ),
                    "mood": "thinking",
                }

            if market_open <= now < market_close:
                wait = _format_duration(market_close - now)
                return {
                    "label": "Market Open",
                    "emoji": "🟢",
                    "detail": f"Closes in {wait}",
                    "assistant_message": (
                        "Friend... the bell rang. Let's see what the market is doing."
                    ),
                    "mood": "success",
                }

            next_rows = schedule[schedule["market_open"] > now]
            next_open = (
                next_rows.iloc[0]["market_open"]
                .tz_convert(EASTERN)
                .to_pydatetime()
            )

            return {
                "label": "After-Hours",
                "emoji": "🔵",
                "detail": f"Reopens {next_open.strftime('%A at %-I:%M %p ET')}",
                "assistant_message": (
                    "Regular trading is over, but we can still prepare "
                    "for the next bell."
                ),
                "mood": "idle",
            }

        next_rows = schedule[schedule["market_open"] > now]

        if not next_rows.empty:
            next_open = (
                next_rows.iloc[0]["market_open"]
                .tz_convert(EASTERN)
                .to_pydatetime()
            )

            return {
                "label": "Market Closed",
                "emoji": "🔴",
                "detail": f"Reopens {next_open.strftime('%A at %-I:%M %p ET')}",
                "assistant_message": (
                    "The market's asleep. Doesn't mean we can't prepare."
                ),
                "mood": "idle",
            }

    except Exception:
        pass

    weekday = now.weekday()
    open_time = datetime.combine(now.date(), time(9, 30), EASTERN)
    close_time = datetime.combine(now.date(), time(16, 0), EASTERN)

    if weekday >= 5:
        next_open = _next_weekday_open(now)
        return {
            "label": "Market Closed",
            "emoji": "🔴",
            "detail": f"Reopens {next_open.strftime('%A at %-I:%M %p ET')}",
            "assistant_message": (
                "The market's asleep. Doesn't mean we can't prepare."
            ),
            "mood": "idle",
        }

    if now < open_time:
        wait = _format_duration(open_time - now)
        return {
            "label": "Pre-Market",
            "emoji": "🟡",
            "detail": f"Opens in {wait}",
            "assistant_message": (
                f"Coffee's brewing... Wall Street wakes up in {wait}."
            ),
            "mood": "thinking",
        }

    if now < close_time:
        wait = _format_duration(close_time - now)
        return {
            "label": "Market Open",
            "emoji": "🟢",
            "detail": f"Closes in {wait}",
            "assistant_message": (
                "Friend... the bell rang. Let's see what the market is doing."
            ),
            "mood": "success",
        }

    next_open = _next_weekday_open(now)
    return {
        "label": "After-Hours",
        "emoji": "🔵",
        "detail": f"Reopens {next_open.strftime('%A at %-I:%M %p ET')}",
        "assistant_message": (
            "Regular trading is over, but we can still prepare "
            "for the next bell."
        ),
        "mood": "idle",
    }


def display_market_status(status: dict) -> None:
    """Display a compact market-status panel in Streamlit."""
    st.markdown(
        f"""
<div style="
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:16px;
    padding:12px 16px;
    margin:8px 0 18px 0;
    border:1px solid rgba(255,255,255,0.12);
    border-radius:14px;
    background:rgba(255,255,255,0.04);
">
    <div style="font-weight:700;">
        {status['emoji']} {status['label']}
    </div>
    <div style="color:#a7a7a7;font-size:0.9rem;text-align:right;">
        {status['detail']}
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

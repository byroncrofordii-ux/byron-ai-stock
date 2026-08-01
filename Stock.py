import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import streamlit.components.v1 as components
import json
import os
import hashlib

import sys
from pathlib import Path

PROJECT_FOLDER = Path(__file__).resolve().parent

if str(PROJECT_FOLDER) not in sys.path:
    sys.path.insert(0, str(PROJECT_FOLDER))

from modules.scoring import calculate_stock_score
from modules.forecasting import generate_probability_forecast

USERS_FILE = "users.json"
WATCHLIST_FOLDER = "watchlists"

DEFAULT_MARKET_TICKERS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "JPM",
    "V",
    "WMT",
    "DIS",
    "KO",
]

HOT_MARKET_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL",
    "META", "TSLA", "AVGO", "NFLX", "AMD",
    "PLTR", "INTC", "CRM", "ORCL", "ADBE",
    "JPM", "BAC", "GS", "V", "MA",
    "WMT", "COST", "TGT", "HD", "LOW",
    "DIS", "NKE", "KO", "PEP", "MCD",
    "XOM", "CVX", "CAT", "BA", "GE",
    "UNH", "JNJ", "PFE", "ABBV", "MRK",
]

def normalize_username(username: str) -> str:
    """
    Make usernames consistent and safe for filenames.
    """
    username = username.strip().lower()
    return "".join(
        character
        for character in username
        if character.isalnum() or character in ("_", "-")
    )


def hash_pin(pin: str) -> str:
    """
    Store a protected version of the PIN instead of the actual PIN.
    """
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


def load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def save_users(users: dict) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4)


def create_user(username: str, pin: str) -> tuple[bool, str]:
    username = normalize_username(username)

    if not username:
        return False, "Please enter a valid username."

    if not pin.isdigit() or len(pin) != 4:
        return False, "Your PIN must contain exactly four numbers."

    users = load_users()

    if username in users:
        return False, "That username already exists."

    users[username] = {
        "pin_hash": hash_pin(pin)
    }

    save_users(users)
    save_watchlist(username, [])

    return True, "Your B.Y.R.O.N. profile was created."


def verify_user(username: str, pin: str) -> bool:
    username = normalize_username(username)
    users = load_users()

    if username not in users:
        return False

    saved_hash = users[username].get("pin_hash", "")
    return saved_hash == hash_pin(pin)


def get_watchlist_file(username: str) -> str:
    os.makedirs(WATCHLIST_FOLDER, exist_ok=True)

    safe_username = normalize_username(username)

    return os.path.join(
        WATCHLIST_FOLDER,
        f"{safe_username}.json",
    )


def load_watchlist(username: str) -> list:
    watchlist_file = get_watchlist_file(username)

    if not os.path.exists(watchlist_file):
        return []

    try:
        with open(watchlist_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []


def save_watchlist(username: str, watchlist: list) -> None:
    watchlist_file = get_watchlist_file(username)

    cleaned_watchlist = sorted(
        set(stock.strip().upper() for stock in watchlist if stock.strip())
    )

    with open(watchlist_file, "w", encoding="utf-8") as file:
        json.dump(cleaned_watchlist, file, indent=4)


def add_stock(username: str, ticker: str) -> None:
    watchlist = load_watchlist(username)
    ticker = ticker.strip().upper()

    if ticker and ticker not in watchlist:
        watchlist.append(ticker)
        save_watchlist(username, watchlist)


def remove_stock(username: str, ticker: str) -> None:
    watchlist = load_watchlist(username)
    ticker = ticker.strip().upper()

    if ticker in watchlist:
        watchlist.remove(ticker)
        save_watchlist(username, watchlist)


COMPANY_TO_TICKER = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "meta": "META",
    "facebook": "META",
    "netflix": "NFLX",
    "amd": "AMD",
    "palantir": "PLTR",
    "disney": "DIS",
    "walmart": "WMT",
    "target": "TGT",
    "coca cola": "KO",
    "coke": "KO",
    "nike": "NKE",
    "intel": "INTC",
    "salesforce": "CRM",
}

def resolve_ticker(search_text: str) -> str:
    """
    Convert a company name or ticker into a ticker symbol.
    """
    cleaned_text = search_text.strip().lower()

    if cleaned_text in COMPANY_TO_TICKER:
        return COMPANY_TO_TICKER[cleaned_text]

    return search_text.strip().upper()

# ---------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------
st.set_page_config(
    page_title="B.Y.R.O.N.",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------
# CUSTOM DESIGN
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {
            max-width: 900px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        .app-subtitle {
            color: #a7a7a7;
            font-size: 1.05rem;
            margin-top: -15px;
            margin-bottom: 25px;
        }

        .result-card {
            background-color: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 18px;
            padding: 22px;
            margin-top: 18px;
            margin-bottom: 18px;
        }

        .signal-card {
            border-radius: 18px;
            padding: 26px;
            text-align: center;
            margin-top: 20px;
            margin-bottom: 20px;
        }

        .signal-title {
            font-size: 0.95rem;
            letter-spacing: 2px;
            opacity: 0.85;
        }

        .signal-value {
            font-size: 2.3rem;
            font-weight: 800;
            margin-top: 8px;
        }

        .signal-message {
            font-size: 1.05rem;
            margin-top: 10px;
        }

        .buy-card {
            background: rgba(35, 180, 95, 0.18);
            border: 1px solid rgba(35, 180, 95, 0.55);
        }

        .watch-card {
            background: rgba(245, 180, 35, 0.18);
            border: 1px solid rgba(245, 180, 35, 0.55);
        }

        .avoid-card {
            background: rgba(230, 65, 65, 0.18);
            border: 1px solid rgba(230, 65, 65, 0.55);
        }

        .small-note {
            color: #9c9c9c;
            font-size: 0.82rem;
            margin-top: 22px;
        }

        div.stButton > button {
            width: 100%;
            border-radius: 12px;
            height: 3rem;
            font-weight: 700;
        }

                .ticker-title {
            font-size: 0.85rem;
            font-weight: 700;
            margin-bottom: 6px;
            opacity: 0.85;
        }

        .ticker-wrapper {
            width: 100%;
            overflow: hidden;
            white-space: nowrap;
            border-top: 1px solid rgba(255, 255, 255, 0.12);
            border-bottom: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(255, 255, 255, 0.04);
            padding: 10px 0;
            margin-bottom: 22px;
        }

        .ticker-scroll {
            display: inline-flex;
            align-items: center;
            white-space: nowrap;
            width: max-content;
            animation: ticker-move 45s linear infinite;
        }

        .ticker-item {
            display: inline-block;
            margin-right: 42px;
            font-size: 15px;
            color: #ffffff;
        }

        .ticker-up {
            color: #39d98a;
            margin-left: 4px;
        }

        .ticker-down {
            color: #ff6b6b;
            margin-left: 4px;
        }

        .ticker-flat {
            color: #b8b8b8;
            margin-left: 4px;
        }

        @keyframes ticker-move {
            from {
                transform: translateX(100%);
            }

            to {
                transform: translateX(-100%);
            }
        }

        .ticker-wrapper:hover .ticker-scroll {
            animation-play-state: paused;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# DATA FUNCTIONS
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def get_marquee_data(tickers: tuple[str, ...]) -> list[dict]:
    """
    Get the latest price and daily percentage change
    for the scrolling stock ticker.
    """

    marquee_items = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)

            history = stock.history(
                period="5d",
                interval="1d",
                auto_adjust=True,
            )

            if history.empty or len(history) < 2:
                continue

            current_price = float(history["Close"].iloc[-1])
            previous_price = float(history["Close"].iloc[-2])

            daily_change = (
                ((current_price - previous_price) / previous_price) * 100
                if previous_price != 0
                else 0
            )

            marquee_items.append(
                {
                    "ticker": ticker,
                    "price": current_price,
                    "change": daily_change,
                }
            )

        except Exception:
            continue

    return marquee_items

@st.cache_data(ttl=300)
def get_hot_stocks(
    tickers: tuple[str, ...],
    limit: int = 10,
) -> list[dict]:
    """
    Rank stocks by their most recent daily percentage gain.
    """

    hot_stocks = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)

            history = stock.history(
                period="5d",
                interval="1d",
                auto_adjust=True,
            )

            if history.empty or len(history) < 2:
                continue

            current_price = float(history["Close"].iloc[-1])
            previous_close = float(history["Close"].iloc[-2])

            if previous_close == 0:
                continue

            percentage_change = (
                (current_price - previous_close)
                / previous_close
            ) * 100

            hot_stocks.append(
                {
                    "ticker": ticker,
                    "price": current_price,
                    "previous_close": previous_close,
                    "change": percentage_change,
                }
            )

        except Exception:
            continue

    # Highest daily percentage gain appears first
    hot_stocks.sort(
        key=lambda item: item["change"],
        reverse=True,
    )

    return hot_stocks[:limit]

@st.cache_data(ttl=300)


@st.cache_data(ttl=300)
def get_hidden_gems(
    tickers: tuple[str, ...],
    limit: int = 5,
    maximum_price: float = 50,
) -> list[dict]:
    """
    Find lower-priced stocks showing strong recent growth.

    A hidden gem must:
    - Cost no more than maximum_price
    - Have positive growth over roughly 30 trading days
    """

    hidden_gems = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)

            history = stock.history(
                period="3mo",
                interval="1d",
                auto_adjust=True,
            )

            if history.empty or len(history) < 22:
                continue

            latest_price = float(history["Close"].iloc[-1])
            price_30_days_ago = float(history["Close"].iloc[-22])

            if latest_price > maximum_price or price_30_days_ago <= 0:
                continue

            growth_30d = (
                (latest_price - price_30_days_ago)
                / price_30_days_ago
            ) * 100

            if growth_30d <= 0:
                continue

            hidden_gems.append(
                {
                    "ticker": ticker,
                    "price": latest_price,
                    "growth_30d": growth_30d,
                }
            )

        except Exception:
            continue

    hidden_gems.sort(
        key=lambda item: item["growth_30d"],
        reverse=True,
    )

    return hidden_gems[:limit]




def display_market_marquee(
    tickers: list[str],
    title: str,
) -> None:
    """
    Display a scrolling stock ticker from right to left.
    """

    if not tickers:
        return

    marquee_data = get_marquee_data(tuple(tickers))

    if not marquee_data:
        return

    marquee_parts = []

    for item in marquee_data:
        change = item["change"]

        if change > 0:
            movement = f"▲ {change:+.2f}%"
            movement_class = "ticker-up"
        elif change < 0:
            movement = f"▼ {change:+.2f}%"
            movement_class = "ticker-down"
        else:
            movement = "— 0.00%"
            movement_class = "ticker-flat"

        marquee_parts.append(
            f"""
            <span class="ticker-item">
                <strong>{item['ticker']}</strong>
                ${item['price']:,.2f}
                <span class="{movement_class}">
                    {movement}
                </span>
            </span>
            """
        )

    ticker_html = "".join(marquee_parts)

    full_html = f"""
    <html>
    <head>
        <style>
            html,
            body {{
                margin: 0;
                padding: 0;
                background: #0e1117;
                color: #ffffff;
                font-family: Arial, sans-serif;
                overflow: hidden;
            }}

        .ticker-title {{
            color: #ffffff;
        }}

        .ticker-item {{
            color: #ffffff;
        }}

            .ticker-title {{
                font-size: 14px;
                font-weight: 700;
                margin-bottom: 7px;
            }}

            .ticker-wrapper {{
                width: 100%;
                overflow: hidden;
                white-space: nowrap;
                border-top: 1px solid rgba(255, 255, 255, 0.15);
                border-bottom: 1px solid rgba(255, 255, 255, 0.15);
                background: rgba(255, 255, 255, 0.05);
                padding: 12px 0;
            }}

            .ticker-scroll {{
                display: inline-block;
                width: max-content;
                white-space: nowrap;
                animation: ticker-move 60s linear infinite;
            }}

@keyframes ticker-move {{
    from {{
        transform: translateX(0);
    }}

    to {{
        transform: translateX(-50%);
    }}
}}

            .ticker-item {{
                display: inline-block;
                margin-right: 42px;
                font-size: 15px;
            }}

            .ticker-up {{
                color: #39d98a;
                margin-left: 5px;
            }}

            .ticker-down {{
                color: #ff6b6b;
                margin-left: 5px;
            }}

            .ticker-flat {{
                color: #b8b8b8;
                margin-left: 5px;
            }}

        @keyframes ticker-move {{
            0% {{
                transform: translateX(100%);
            }}

            100% {{
                transform: translateX(-100%);
            }}
        }}
        

            .ticker-wrapper:hover .ticker-scroll {{
                animation-play-state: paused;
            }}
        </style>
    </head>

    <body>
        <div class="ticker-title">{title}</div>

        <div class="ticker-wrapper">
            <div class="ticker-scroll">
                {ticker_html}
                {ticker_html}
            </div>
        </div>
    </body>
    </html>
    """

    components.html(
        full_html,
        height=85,
        scrolling=False,
    )

@st.cache_data(ttl=900)
def download_stock_data(ticker: str, period: str) -> pd.DataFrame:
    """
    Download stock history from Yahoo Finance.
    Cache lasts 15 minutes.
    """
    try:
        stock = yf.Ticker(ticker)

        data = stock.history(
            period=period,
            interval="1d",
            auto_adjust=True,
        )

        if data.empty:
            return pd.DataFrame()

        data = data.copy()
        data.dropna(subset=["Close"], inplace=True)

        return data

    except Exception as error:
        raise RuntimeError(
            f"Yahoo Finance error for {ticker}: {error}"
        ) from error


def calculate_rsi(close_prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index.
    """
    price_changes = close_prices.diff()

    gains = price_changes.clip(lower=0)
    losses = -price_changes.clip(upper=0)

    average_gain = gains.rolling(period).mean()
    average_loss = losses.rolling(period).mean()

    relative_strength = average_gain / average_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + relative_strength))

    return rsi



def create_analysis(data: pd.DataFrame) -> dict:
    """
    Convert market calculations into simple friend-friendly results.
    """
    df = data.copy()

    df["Average_20"] = df["Close"].rolling(20).mean()
    df["Average_50"] = df["Close"].rolling(50).mean()
    df["Daily_Return"] = df["Close"].pct_change()
    df["RSI"] = calculate_rsi(df["Close"])

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    current_price = float(latest["Close"])
    previous_price = float(previous["Close"])

    daily_change = (
        ((current_price - previous_price) / previous_price) * 100
        if previous_price != 0
        else 0
    )

    average_20 = float(latest["Average_20"])
    average_50 = float(latest["Average_50"])
    rsi = float(latest["RSI"])

    daily_volatility = df["Daily_Return"].tail(30).std()
    annualized_volatility = float(daily_volatility * np.sqrt(252) * 100)

def scan_green_signals(
    tickers: tuple[str, ...],
) -> list[dict]:
    """
    Scan stocks and return those with a green BYRON signal.
    """

    green_stocks = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)

            history = stock.history(
                period="6mo",
                interval="1d",
                auto_adjust=True,
            )

            if history.empty or len(history) < 55:
                continue

            data = history.copy()
            data["Average_20"] = data["Close"].rolling(20).mean()
            data["Average_50"] = data["Close"].rolling(50).mean()
            data["RSI"] = calculate_rsi(data["Close"])

            latest = data.iloc[-1]

            current_price = float(latest["Close"])
            average_20 = float(latest["Average_20"])
            average_50 = float(latest["Average_50"])
            rsi = float(latest["RSI"])
            recent_return = data["Close"].pct_change(5).iloc[-1]

            score_results = calculate_stock_score(
                current_price=current_price,
                average_20=average_20,
                average_50=average_50,
                rsi=rsi,
                recent_return=recent_return,
            )

            if score_results["score"] >= 68:
                green_stocks.append(
                    {
                        "ticker": ticker,
                        "price": current_price,
                        "score": score_results["score"],
                        "signal": score_results["signal"],
                        "reason": score_results["reason"],
                    }
                )

        except Exception:
            continue

    green_stocks.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return green_stocks


    # -----------------------------------------------------
    # SIGNAL SCORE
    # -----------------------------------------------------
    recent_return = df["Close"].pct_change(5).iloc[-1]

    score_results = calculate_stock_score(
        current_price=current_price,
        average_20=average_20,
        average_50=average_50,
        rsi=rsi,
        recent_return=recent_return,
    )

    score = score_results["score"]
    signal = score_results["signal"]
    emoji = score_results["emoji"]
    card_class = score_results["card_class"]
    action_message = score_results["action_message"]
    confidence = score_results["confidence"]
    plain_reason = score_results["reason"]

    # -----------------------------------------------------
    # RISK LEVEL
    # -----------------------------------------------------
    if annualized_volatility < 25:
        risk = "Low"
        risk_emoji = "🟢"
    elif annualized_volatility < 50:
        risk = "Medium"
        risk_emoji = "🟡"
    else:
        risk = "High"
        risk_emoji = "🔴"


    return {
        "data": df,
        "current_price": current_price,
        "daily_change": daily_change,
        "average_20": average_20,
        "average_50": average_50,
        "rsi": rsi,
        "volatility": annualized_volatility,
        "score": score,
        "signal": signal,
        "emoji": emoji,
        "card_class": card_class,
        "action_message": action_message,
        "risk": risk,
        "risk_emoji": risk_emoji,
        "confidence": confidence,
        "reason": plain_reason,
    }


# ---------------------------------------------------------
# LOGIN SYSTEM
# ---------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "username" not in st.session_state:
    st.session_state["username"] = ""


def log_in_user(username: str) -> None:
    st.session_state["logged_in"] = True
    st.session_state["username"] = normalize_username(username)
    st.session_state.pop("selected_stock", None)


def log_out_user() -> None:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state.pop("selected_stock", None)


if not st.session_state["logged_in"]:
    st.title("📈 B.Y.R.O.N.")

    st.markdown(
        """
        <div class="app-subtitle">
            Behavioral Yield & Risk Optimization Network<br>
            <strong>Welcome to the party.</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_tab, create_tab = st.tabs(
        ["Log In", "Create Profile"]
    )

    with login_tab:
        login_username = st.text_input(
            "Username",
            key="login_username",
        )

        login_pin = st.text_input(
            "4-digit PIN",
            type="password",
            max_chars=4,
            key="login_pin",
        )

        if st.button(
            "Enter B.Y.R.O.N.",
            type="primary",
            use_container_width=True,
        ):
            if verify_user(login_username, login_pin):
                log_in_user(login_username)
                st.rerun()
            else:
                st.error("The username or PIN is incorrect.")

    with create_tab:
        new_username = st.text_input(
            "Choose a username",
            key="new_username",
        )

        new_pin = st.text_input(
            "Choose a 4-digit PIN",
            type="password",
            max_chars=4,
            key="new_pin",
        )

        confirm_pin = st.text_input(
            "Confirm your PIN",
            type="password",
            max_chars=4,
            key="confirm_pin",
        )

        if st.button(
            "Create Profile",
            use_container_width=True,
        ):
            if new_pin != confirm_pin:
                st.error("The PINs do not match.")
            else:
                created, message = create_user(
                    new_username,
                    new_pin,
                )

                if created:
                    st.success(message)
                    log_in_user(new_username)
                    st.rerun()
                else:
                    st.error(message)

    st.stop()


# ---------------------------------------------------------
# APP HEADER
# ---------------------------------------------------------
st.title("📈 B.Y.R.O.N.")

st.markdown(
    """
    <div class="app-subtitle">
        Behavioral Yield & Risk Optimization Network<br>
        <strong>See Tomorrow's Trends Today.</strong>
    </div>
    """,
    unsafe_allow_html=True,
)

##################LOGIN/LOGOUT BUTTON#################

current_user = st.session_state["username"]

user_column, logout_column = st.columns([3, 1])

user_column.caption(
    f"Signed in as @{current_user}"
)

if logout_column.button(
    "Log Out",
    use_container_width=True,
):
    log_out_user()
    st.rerun()

##################WATCHLIST############################

watchlist = load_watchlist(current_user)

if watchlist:
    marquee_tickers = watchlist
    marquee_title = "⭐ Your Watchlist"
else:
    marquee_tickers = DEFAULT_MARKET_TICKERS
    marquee_title = "🌎 Nasdaq & Dow Market Watch"

display_market_marquee(
    marquee_tickers,
    marquee_title,
)

# ---------------------------------------------------------
# MARKET DISCOVERY
# ---------------------------------------------------------

if watchlist:
    discovery_pool = watchlist
    discovery_source = "Your Watchlist"
else:
    discovery_pool = HOT_MARKET_TICKERS
    discovery_source = "The Market"


# ---------------------------------------------------------
# WHAT'S HOT
# ---------------------------------------------------------
with st.expander(
    f"🔥 What's Hot — {discovery_source}",
    expanded=False,
):
    st.caption(
        "Stocks showing the strongest recent price growth."
    )

    with st.spinner("B.Y.R.O.N. is checking market momentum..."):
        hot_stocks = get_hot_stocks(
            tuple(discovery_pool),
            limit=5,
        )

    if not hot_stocks:
        st.info(
            "Market movement is not available right now."
        )

    else:
        for position, stock in enumerate(
            hot_stocks,
            start=1,
        ):
            ticker_column, price_column, change_column = st.columns(
                [1.2, 1.4, 1.3]
            )

            with ticker_column:
                if st.button(
                    f"{position}. {stock['ticker']}",
                    key=f"hot_{stock['ticker']}",
                    use_container_width=True,
                ):
                    st.session_state["selected_stock"] = stock["ticker"]
                    st.rerun()

            price_column.metric(
                "Latest Close",
                f"${stock['price']:,.2f}",
            )

            change_column.metric(
                "Daily Growth",
                f"{stock['change']:+.2f}%",
            )


# ---------------------------------------------------------
# HIDDEN GEMS
# ---------------------------------------------------------
with st.expander(
    f"💎 Hidden Gems — {discovery_source}",
    expanded=False,
):
    st.caption(
        "Lower-priced stocks showing strong recent growth."
    )

    with st.spinner("B.Y.R.O.N. is searching for hidden gems..."):
        hidden_gems = get_hidden_gems(
            tuple(discovery_pool),
            limit=5,
            maximum_price=50,
        )

    if not hidden_gems:
        st.info(
            "No hidden gems met the current requirements."
        )

    else:
        for position, stock in enumerate(
            hidden_gems,
            start=1,
        ):
            ticker_column, price_column, growth_column = st.columns(
                [1.2, 1.4, 1.3]
            )

            with ticker_column:
                if st.button(
                    f"{position}. {stock['ticker']}",
                    key=f"gem_{stock['ticker']}",
                    use_container_width=True,
                ):
                    st.session_state["selected_stock"] = stock["ticker"]
                    st.rerun()

            price_column.metric(
                "Latest Close",
                f"${stock['price']:,.2f}",
            )

            growth_column.metric(
                "30-Day Growth",
                f"{stock['growth_30d']:+.2f}%",
            )

with st.expander(
    "🟢 Find Current Green Signals",
    expanded=False,
):
    st.caption(
        "B.Y.R.O.N. scans the market list for stocks currently "
        "scoring 68 or higher."
    )

    if st.button(
        "Scan for Green Signals",
        use_container_width=True,
    ):
        with st.spinner(
            "B.Y.R.O.N. is scanning the market..."
        ):
            green_signals = scan_green_signals(
                tuple(HOT_MARKET_TICKERS)
            )

        if not green_signals:
            st.info(
                "No stocks in the current market list earned "
                "a green signal right now."
            )

        else:
            st.success(
                f"B.Y.R.O.N. found {len(green_signals)} green signal(s)."
            )

            for position, stock in enumerate(
                green_signals,
                start=1,
            ):
                ticker_column, price_column, score_column = st.columns(
                    [1.2, 1.3, 1.2]
                )

                with ticker_column:
                    if st.button(
                        f"{position}. {stock['ticker']}",
                        key=f"green_signal_{stock['ticker']}",
                        use_container_width=True,
                    ):
                        st.session_state["selected_stock"] = stock["ticker"]
                        st.rerun()

                price_column.metric(
                    "Latest Close",
                    f"${stock['price']:,.2f}",
                )

                score_column.metric(
                    "BYRON Score",
                    f"{stock['score']}/100",
                )

                st.caption(stock["reason"])

st.subheader("⭐ My Watchlist")

if watchlist:
    cols = st.columns(min(5, len(watchlist)))

    for i, stock in enumerate(watchlist):
        if cols[i % len(cols)].button(stock):
            st.session_state["selected_stock"] = stock
else:
    st.caption("No stocks saved yet.")


    


# ---------------------------------------------------------
# SEARCH AREA
# ---------------------------------------------------------
search_text = st.text_input(
    "Enter a company name or stock ticker",
    value=st.session_state.get("selected_stock", "AAPL"),
    placeholder="Examples: Google, Apple, TSLA, NVDA",
)

ticker = resolve_ticker(search_text)

history_period = st.selectbox(
    "How much history should BYRON review?",
    options=["6mo", "1y", "2y", "5y"],
    index=1,
    format_func=lambda value: {
        "6mo": "6 Months",
        "1y": "1 Year",
        "2y": "2 Years",
        "5y": "5 Years",
    }[value],
)

analyze_button = st.button(
    "Analyze Stock",
    type="primary",
    use_container_width=True,
)


# ---------------------------------------------------------
# RESULTS
# ---------------------------------------------------------
if analyze_button:
    if not ticker:
        st.warning("Please enter a stock ticker.")
        st.stop()

    with st.spinner(f"BYRON is checking {ticker}..."):
        try:
            stock_data = download_stock_data(ticker, history_period)

            if stock_data.empty:
                st.error(
                    f"No market data was found for {ticker}. "
                    "Please check the ticker and try again."
                )
                st.stop()

            if len(stock_data) < 55:
                st.error(
                    "There is not enough price history to analyze this stock."
                )
                st.stop()

            results = create_analysis(stock_data)

            forecast = generate_probability_forecast(
                stock_data,
                horizon_days=63,
                simulations=5000,
)

        except Exception as error:
            st.error(
                "BYRON could not retrieve this stock right now. "
                "Please try again in a moment."
            )

            with st.expander("Technical error details"):
                st.code(str(error))

            st.stop()

    st.divider()
    st.subheader(f"{ticker} Market Check")

    price_column, change_column = st.columns(2)

    price_column.metric(
        label="Current Price",
        value=f"${results['current_price']:,.2f}",
    )

    change_column.metric(
        label="Today's Movement",
        value=f"{results['daily_change']:+.2f}%",
    )

    st.markdown(
        f"""
        <div class="signal-card {results['card_class']}">
            <div class="signal-title">BYRON SIGNAL</div>
            <div class="signal-value">
                {results['emoji']} {results['signal']}
            </div>
            <div class="signal-message">
                {results['action_message']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    score_column, confidence_column, risk_column = st.columns(3)

    score_column.metric(
        "BYRON Score",
        f"{results['score']}/100",
    )

    confidence_column.metric(
        "Confidence",
        f"{results['confidence']}%",
    )

    risk_column.metric(
        "Risk Level",
        f"{results['risk_emoji']} {results['risk']}",
    )

    st.markdown("### Why is BYRON saying this?")
    st.info(results["reason"])

    st.markdown("### 📊 90-Day Probability Outlook")

    st.info(
    "🌦️ Just like the weather, nobody can predict the future with certainty. "
    "B.Y.R.O.N. estimates the most likely outcomes based on historical data "
    "and probability—not guarantees."
)

    st.caption(
        "B.Y.R.O.N. simulated 5,000 possible outcomes using the "
        "stock's recent returns and volatility."
    )

    bull_column, base_column, bear_column = st.columns(3)

    bull_column.metric(
    "☀️ Bull Case",
    f"{forecast['bull_return']:+.1f}%",
    f"{forecast['bull_probability']:.1f}% probability",
    help=(
        "☀️ Think of this as a sunny day. "
        "Everything goes right, and this is the best-case outcome "
        "B.Y.R.O.N. sees over the next 90 days."
    ),
)

    base_column.metric(
        "🌤️ Base Case",
        f"{forecast['base_return']:+.1f}%",
        f"{forecast['base_probability']:.1f}% probability",
        help=(
            "🌤️ Think of this as partly cloudy. "
            "Nothing amazing, nothing terrible. This is the outcome "
            "B.Y.R.O.N. believes is most likely."
        ),
    )

    bear_column.metric(
        "🌧️ Bear Case",
        f"{forecast['bear_return']:+.1f}%",
        f"{forecast['bear_probability']:.1f}% probability",
        help=(
            "🌧️ Think of this as a rainy day. "
            "If things don't go as planned, this is the downside "
            "scenario B.Y.R.O.N. is preparing for."
    ),
)


    st.progress(
        int(
            max(
                0,
                min(
                    100,
                    forecast["probability_positive"],
                ),
            )
        ),
        text=(
            "Estimated probability of finishing higher: "
            f"{forecast['probability_positive']:.1f}%"
        ),
    )

    with st.expander("How was this forecast calculated?"):
        st.write(
            "B.Y.R.O.N. reviewed the stock's recent daily returns "
            "and volatility, then simulated 5,000 possible price "
            "paths covering approximately 90 calendar days."
        )

        st.write(
            "**Bull case:** simulated return above 10%."
        )

        st.write(
            "**Base case:** simulated return between -5% and +10%."
        )

        st.write(
            "**Bear case:** simulated return below -5%."
        )

        st.warning(
            "This is an educational probability estimate based on "
            "historical behavior. It is not a guarantee of future "
            "performance or financial advice."
        )

    st.markdown("### Price History")


    chart_data = results["data"][["Close"]].copy()
    chart_data.rename(columns={"Close": f"{ticker} Price"}, inplace=True)

    st.line_chart(
        chart_data,
        use_container_width=True,
        height=350,
    )

    with st.expander("See More Details"):
        detail_one, detail_two = st.columns(2)

        detail_one.metric(
            "20-Day Average",
            f"${results['average_20']:,.2f}",
        )

        detail_two.metric(
            "50-Day Average",
            f"${results['average_50']:,.2f}",
        )

        detail_three, detail_four = st.columns(2)

        detail_three.metric(
            "Momentum Reading",
            f"{results['rsi']:.1f}",
        )

        detail_four.metric(
            "Price Movement",
            f"{results['volatility']:.1f}%",
        )

        st.caption(
            "Momentum readings below 30 may indicate heavy selling. "
            "Readings above 70 may indicate the price has increased quickly."
        )

st.divider()


if ticker in watchlist:
    if st.button(
        "❌ Remove from Watchlist",
        use_container_width=True,
    ):
        remove_stock(current_user, ticker)
        st.success(f"{ticker} was removed from your watchlist.")
        st.rerun()
else:
    if st.button(
        "⭐ Add to Watchlist",
        type="primary",
        use_container_width=True,
    ):
        add_stock(current_user, ticker)
        st.success(f"{ticker} was added to your watchlist.")
        st.rerun()


    st.markdown(
        """
        <div class="small-note">
            B.Y.R.O.N. provides educational market analysis and does not provide
            financial advice. Stock prices can rise or fall unexpectedly.
        </div>
        """,
        unsafe_allow_html=True,
    )
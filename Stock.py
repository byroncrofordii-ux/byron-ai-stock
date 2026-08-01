import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import json
import os
import hashlib

import sys
from pathlib import Path

PROJECT_FOLDER = Path(__file__).resolve().parent

if str(PROJECT_FOLDER) not in sys.path:
    sys.path.insert(0, str(PROJECT_FOLDER))

from modules.scoring import calculate_stock_score

USERS_FILE = "users.json"
WATCHLIST_FOLDER = "watchlists"


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
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# DATA FUNCTIONS
# ---------------------------------------------------------
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
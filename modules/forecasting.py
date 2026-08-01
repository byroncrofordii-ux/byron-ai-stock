"""Probability forecasting tools for B.Y.R.O.N."""

import numpy as np
import pandas as pd


def generate_probability_forecast(
    data: pd.DataFrame,
    horizon_days: int = 63,
    simulations: int = 5000,
    seed: int = 42,
) -> dict:
    """
    Simulate possible stock outcomes over approximately 90 calendar days.

    Sixty-three trading days is roughly three calendar months.
    The simulation uses recent historical returns and volatility.
    """

    close_prices = data["Close"].dropna()

    if len(close_prices) < 60:
        raise ValueError(
            "At least 60 trading days are required for a forecast."
        )

    # Use no more than the latest year of trading history.
    recent_prices = close_prices.tail(252)

    log_returns = np.log(
        recent_prices / recent_prices.shift(1)
    ).dropna()

    if log_returns.empty:
        raise ValueError(
            "B.Y.R.O.N. could not calculate historical returns."
        )

    daily_average_return = float(log_returns.mean())
    daily_volatility = float(log_returns.std())

    if not np.isfinite(daily_volatility) or daily_volatility <= 0:
        raise ValueError(
            "B.Y.R.O.N. could not calculate usable volatility."
        )

    # Prevent an unusually strong recent period from creating
    # unrealistic long-range forecasts.
    daily_average_return = float(
        np.clip(
            daily_average_return,
            -0.002,
            0.002,
        )
    )

    current_price = float(recent_prices.iloc[-1])

    random_generator = np.random.default_rng(seed)

    simulated_daily_returns = random_generator.normal(
        loc=daily_average_return,
        scale=daily_volatility,
        size=(simulations, horizon_days),
    )

    simulated_growth = np.exp(
        simulated_daily_returns.sum(axis=1)
    )

    ending_prices = current_price * simulated_growth

    total_returns = (
        ending_prices / current_price
    ) - 1

    # Define the three outcome groups.
    bear_mask = total_returns < -0.05
    base_mask = (
        (total_returns >= -0.05)
        & (total_returns <= 0.10)
    )
    bull_mask = total_returns > 0.10

    bear_probability = float(bear_mask.mean() * 100)
    base_probability = float(base_mask.mean() * 100)
    bull_probability = float(bull_mask.mean() * 100)

    def scenario_return(
        scenario_values: np.ndarray,
        fallback_percentile: float,
    ) -> float:
        """
        Return the middle result for a scenario.
        Use a percentile fallback if that group has no simulations.
        """
        if scenario_values.size:
            return float(
                np.median(scenario_values) * 100
            )

        return float(
            np.percentile(
                total_returns,
                fallback_percentile,
            )
            * 100
        )

    bear_return = scenario_return(
        total_returns[bear_mask],
        15,
    )

    base_return = scenario_return(
        total_returns[base_mask],
        50,
    )

    bull_return = scenario_return(
        total_returns[bull_mask],
        85,
    )

    probability_positive = float(
        (total_returns > 0).mean() * 100
    )

    expected_return = float(
        total_returns.mean() * 100
    )

    return {
        "horizon_days": horizon_days,
        "simulations": simulations,
        "current_price": current_price,
        "bull_return": bull_return,
        "bull_probability": bull_probability,
        "base_return": base_return,
        "base_probability": base_probability,
        "bear_return": bear_return,
        "bear_probability": bear_probability,
        "probability_positive": probability_positive,
        "expected_return": expected_return,
    }
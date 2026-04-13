"""Fare calculation engine."""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from app.models import FareRule, PassengerType


def calculate_fare(
    rule: FareRule,
    distance_km: float = 0.0,
) -> Decimal:
    """
    Compute the total fare for a journey given a matching FareRule.

    Args:
        rule: The matched FareRule.
        distance_km: Journey distance in kilometres (used if the rule has a per_km_rate).

    Returns:
        Total fare as a Decimal, rounded to 2 decimal places.
    """
    total = rule.base_fare
    if rule.per_km_rate and distance_km > 0:
        total += rule.per_km_rate * Decimal(str(distance_km))
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def is_peak_time(rule: FareRule, at: datetime | None = None) -> bool:
    """
    Determine whether the given time falls within the rule's peak window.
    Returns True if peak times are defined and the time is within them.
    Returns False if no peak times are defined.
    """
    if rule.peak_start is None or rule.peak_end is None:
        return False
    if at is None:
        at = datetime.now(timezone.utc)
    current_time = at.time()
    if rule.peak_start <= rule.peak_end:
        return rule.peak_start <= current_time <= rule.peak_end
    # Wraps midnight
    return current_time >= rule.peak_start or current_time <= rule.peak_end


def find_matching_rule(
    rules: list[FareRule],
    origin_zone: str | None,
    destination_zone: str | None,
    passenger_type: PassengerType,
    at: datetime | None = None,
) -> FareRule | None:
    """
    Find the highest-priority fare rule that matches the given journey parameters.
    Rules are evaluated in descending priority order.
    """
    candidates = sorted(rules, key=lambda r: r.priority, reverse=True)
    for rule in candidates:
        if not rule.is_active:
            continue
        if rule.origin_zone and rule.origin_zone != origin_zone:
            continue
        if rule.destination_zone and rule.destination_zone != destination_zone:
            continue
        if rule.passenger_type and rule.passenger_type != passenger_type:
            continue
        return rule
    return None

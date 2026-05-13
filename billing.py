"""
Billing module for parking system.
Implements tiered fee structure:
- 0-55 minutes: FREE
- 56-120 minutes: Rs 50 (1 hour)
- 121-180 minutes: Rs 100 (2 hours)
- 181+ minutes: Rs 100 + Rs 50 per additional hour (ceil)
"""

from datetime import datetime
import math
from typing import Tuple

RATE_PER_HOUR = 50
FREE_MINUTES = 55
TIER_1_MAX = 120  # Rs 50
TIER_2_MAX = 180  # Rs 100
TIER_2_RATE = 100  # Rs 100 for 2 hours
TIER_3_RATE = 50   # Rs 50 per additional hour


def calc_amount(entry_iso: str, exit_iso: str) -> Tuple[int, float, int]:
    """
    Calculate parking fee based on entry and exit times.
    
    Args:
        entry_iso: ISO format entry timestamp
        exit_iso: ISO format exit timestamp
        
    Returns:
        (amount_rs: int, actual_duration_hours: float, billable_hours: int)
    """
    try:
        entry_dt = datetime.fromisoformat(entry_iso)
        exit_dt = datetime.fromisoformat(exit_iso)
    except ValueError:
        return 0, 0.0, 0
    
    minutes = (exit_dt - entry_dt).total_seconds() / 60.0
    if minutes < 0:
        minutes = 0
    
    hours = minutes / 60.0
    
    # Tier 1: 0-55 minutes FREE
    if minutes <= FREE_MINUTES:
        return 0, hours, 0
    
    # Tier 2: 56-120 minutes = Rs 50
    if minutes <= TIER_1_MAX:
        return RATE_PER_HOUR, hours, 1
    
    # Tier 3: 121-180 minutes = Rs 100
    if minutes <= TIER_2_MAX:
        return TIER_2_RATE, hours, 2
    
    # Tier 4: 181+ minutes = Rs 100 + Rs 50 per additional started hour
    billable_minutes = minutes - TIER_2_MAX
    additional_hours = math.ceil(billable_minutes / 60.0)
    amount = TIER_2_RATE + (additional_hours * TIER_3_RATE)
    billable_hours = 2 + additional_hours
    
    return amount, hours, billable_hours
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil, floor
from typing import Any


def calculate_percentage(
    present: int,
    absent: int,
    late: int,
    excused: int = 0,
    *,
    late_counts_as_attended: bool = True,
    excused_counts_in_denominator: bool = False,
) -> Decimal:
    attended = present + (late if late_counts_as_attended else 0)
    counted = present + absent + late
    if excused_counts_in_denominator:
        counted += excused
    if counted <= 0:
        return Decimal("0.00")
    return (Decimal(attended) * Decimal("100") / Decimal(counted)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def recovery_required(
    attended: int,
    counted: int,
    target_percentage: Decimal | float | int,
    future_classes_available: int | None = None,
) -> dict[str, Any]:
    target = Decimal(str(target_percentage))
    if not 0 <= target <= 100:
        raise ValueError("target_percentage must be between 0 and 100")
    if attended < 0 or counted < 0 or attended > counted:
        raise ValueError("attended/counts are invalid")

    current = (
        Decimal(attended) * Decimal("100") / Decimal(counted)
        if counted
        else Decimal("0")
    )
    current = current.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if current >= target and counted > 0:
        required = 0
        recoverable = True
    elif counted == 0:
        required = 0 if target == 0 else 1
        recoverable = (
            required == 0
            or future_classes_available is None
            or required <= max(0, future_classes_available)
        )
    elif target == 100:
        required = None
        recoverable = False
    else:
        ratio = target / Decimal("100")
        x = ceil(
            (ratio * Decimal(counted) - Decimal(attended))
            / (Decimal("1") - ratio)
        )
        required = max(0, x)
        recoverable = (
            future_classes_available is None
            or required <= max(0, future_classes_available)
        )

    return {
        "current_percentage": current,
        "target_percentage": target.quantize(Decimal("0.01")),
        "classes_required": required,
        "future_classes_available": future_classes_available,
        "is_recoverable": recoverable,
    }


def maximum_future_absences(
    attended: int,
    counted: int,
    target_percentage: Decimal | float | int,
    future_classes_available: int | None = None,
) -> dict[str, Any]:
    target = Decimal(str(target_percentage))
    if not 0 <= target <= 100:
        raise ValueError("target_percentage must be between 0 and 100")
    if attended < 0 or counted < 0 or attended > counted:
        raise ValueError("attended/counts are invalid")

    current = (
        Decimal(attended) * Decimal("100") / Decimal(counted)
        if counted
        else Decimal("0")
    )
    current = current.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if target == 0:
        maximum = future_classes_available if future_classes_available is not None else None
    elif current < target:
        maximum = 0
    else:
        raw = floor(
            Decimal(attended) / (target / Decimal("100"))
            - Decimal(counted)
        )
        maximum = max(0, raw)
        if future_classes_available is not None:
            maximum = min(maximum, max(0, future_classes_available))

    return {
        "current_percentage": current,
        "target_percentage": target.quantize(Decimal("0.01")),
        "maximum_future_absences": maximum,
        "future_classes_available": future_classes_available,
        "is_currently_compliant": current >= target,
    }

from decimal import Decimal

import pytest

from app.services.attendance_calculations import (
    calculate_percentage,
    maximum_future_absences,
    recovery_required,
)


def test_percentage_basic():
    assert calculate_percentage(8, 2, 0) == Decimal("80.00")


def test_percentage_late_counts_by_default():
    assert calculate_percentage(8, 1, 1) == Decimal("90.00")


def test_percentage_late_can_be_excluded():
    assert calculate_percentage(8, 1, 1, late_counts_as_attended=False) == Decimal("80.00")


def test_excused_is_excluded_by_default():
    assert calculate_percentage(8, 1, 0, excused=5) == Decimal("88.89")


def test_excused_can_count_in_denominator():
    assert calculate_percentage(8, 1, 0, excused=1, excused_counts_in_denominator=True) == Decimal("80.00")


def test_zero_sessions():
    assert calculate_percentage(0, 0, 0) == Decimal("0.00")


@pytest.mark.parametrize(
    ("attended", "counted", "target", "expected"),
    [
        (8, 10, 75, 0),
        (7, 10, 75, 2),
        (6, 10, 75, 6),
        (0, 0, 75, 1),
    ],
)
def test_recovery_required(attended, counted, target, expected):
    result = recovery_required(attended, counted, target)
    assert result["classes_required"] == expected


def test_recovery_is_limited_by_future_classes():
    result = recovery_required(6, 10, 75, future_classes_available=5)
    assert result["classes_required"] == 6
    assert result["is_recoverable"] is False


def test_target_100_with_previous_absence_is_not_recoverable():
    result = recovery_required(8, 10, 100)
    assert result["classes_required"] is None
    assert result["is_recoverable"] is False


def test_zero_history_can_reach_100_with_one_future_class():
    result = recovery_required(0, 0, 100, future_classes_available=1)
    assert result["classes_required"] == 1
    assert result["is_recoverable"] is True


def test_already_at_target_needs_zero_classes():
    result = recovery_required(15, 20, 75)
    assert result["classes_required"] == 0
    assert result["is_recoverable"] is True


@pytest.mark.parametrize(
    ("attended", "counted", "target", "expected"),
    [
        (15, 20, 75, 0),
        (16, 20, 75, 1),
        (10, 10, 75, 3),
        (0, 0, 75, 0),
    ],
)
def test_maximum_future_absences(attended, counted, target, expected):
    result = maximum_future_absences(attended, counted, target)
    assert result["maximum_future_absences"] == expected


def test_maximum_absences_respects_future_limit():
    result = maximum_future_absences(15, 20, 75, future_classes_available=1)
    assert result["maximum_future_absences"] == 0


def test_target_zero_allows_all_available_future_absences():
    result = maximum_future_absences(0, 0, 0, future_classes_available=10)
    assert result["maximum_future_absences"] == 10


def test_below_target_cannot_miss_future_class_and_stay_compliant():
    result = maximum_future_absences(6, 10, 75, future_classes_available=10)
    assert result["maximum_future_absences"] == 0


def test_invalid_attendance_counts():
    with pytest.raises(ValueError):
        recovery_required(11, 10, 75)

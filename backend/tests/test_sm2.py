"""Tests for SM-2 scheduling algorithm.

Covers all quality levels (0-5) and edge cases per Issue #10 requirements.
Target: >= 90% test coverage for SM-2 calculation logic.
"""

from __future__ import annotations

import pytest

from memory_palace.services.scheduling import SchedulingResult, SM2Strategy

# Default SM-2 parameters for a new item
DEFAULT_EASE = 2.5
DEFAULT_INTERVAL = 1
DEFAULT_REPS = 0


@pytest.fixture
def strategy() -> SM2Strategy:
    """Create an SM2Strategy instance."""
    return SM2Strategy()


class TestSM2Quality5:
    """quality=5: Perfect, instant recall."""

    def test_first_review_perfect(self, strategy):
        """First perfect review: interval=1, repetitions=1, ease increases."""
        result = strategy.calculate(quality=5, ease_factor=DEFAULT_EASE, interval=DEFAULT_INTERVAL, repetitions=0)
        assert result.repetitions == 1
        assert result.interval == 1
        assert result.ease_factor > DEFAULT_EASE  # EF increases for q=5

    def test_second_review_perfect(self, strategy):
        """Second perfect review: interval=6, repetitions=2."""
        result = strategy.calculate(quality=5, ease_factor=2.6, interval=1, repetitions=1)
        assert result.repetitions == 2
        assert result.interval == 6

    def test_third_review_perfect(self, strategy):
        """Third+ review: interval scales by ease_factor."""
        result = strategy.calculate(quality=5, ease_factor=2.6, interval=6, repetitions=2)
        assert result.repetitions == 3
        # interval = round(6 * 2.7) = round(16.2) = 16 (ease increases to ~2.7)
        assert result.interval > 6


class TestSM2Quality4:
    """quality=4: Correct after hesitation."""

    def test_first_review_q4(self, strategy):
        """q=4 first review: successful, interval=1."""
        result = strategy.calculate(quality=4, ease_factor=DEFAULT_EASE, interval=DEFAULT_INTERVAL, repetitions=0)
        assert result.repetitions == 1
        assert result.interval == 1
        # EF stays approximately the same for q=4
        assert result.ease_factor >= SM2Strategy.MIN_EASE_FACTOR

    def test_subsequent_review_q4(self, strategy):
        """q=4 subsequent: interval scales, ease_factor stays similar."""
        result = strategy.calculate(quality=4, ease_factor=2.5, interval=6, repetitions=2)
        assert result.repetitions == 3
        assert result.interval >= 6


class TestSM2Quality3:
    """quality=3: Correct with significant difficulty."""

    def test_first_review_q3(self, strategy):
        """q=3 first review: passes but ease_factor decreases."""
        result = strategy.calculate(quality=3, ease_factor=DEFAULT_EASE, interval=DEFAULT_INTERVAL, repetitions=0)
        assert result.repetitions == 1
        assert result.interval == 1
        assert result.ease_factor < DEFAULT_EASE  # EF decreases for q=3

    def test_ease_factor_clamped_at_minimum(self, strategy):
        """Ease factor never goes below 1.3 even with repeated q=3."""
        ef = DEFAULT_EASE
        interval = 1
        reps = 0
        # Simulate many q=3 reviews
        for _ in range(20):
            result = strategy.calculate(quality=3, ease_factor=ef, interval=interval, repetitions=reps)
            ef = result.ease_factor
            interval = result.interval
            reps = result.repetitions
        assert ef >= SM2Strategy.MIN_EASE_FACTOR


class TestSM2Quality2:
    """quality=2: Incorrect, but seemed easy to recall."""

    def test_q2_resets_to_relearn(self, strategy):
        """q=2 resets repetitions to 0 and interval to 1."""
        result = strategy.calculate(quality=2, ease_factor=2.5, interval=15, repetitions=5)
        assert result.repetitions == 0
        assert result.interval == 1

    def test_q2_ease_factor_decreases(self, strategy):
        """q=2 decreases ease factor but clamps at minimum."""
        result = strategy.calculate(quality=2, ease_factor=2.5, interval=1, repetitions=0)
        assert result.ease_factor < 2.5
        assert result.ease_factor >= SM2Strategy.MIN_EASE_FACTOR


class TestSM2Quality1:
    """quality=1: Incorrect, but recognized the correct answer."""

    def test_q1_resets(self, strategy):
        """q=1 resets repetitions and interval."""
        result = strategy.calculate(quality=1, ease_factor=2.5, interval=30, repetitions=10)
        assert result.repetitions == 0
        assert result.interval == 1

    def test_q1_ease_factor_drops(self, strategy):
        """q=1 drops ease factor significantly."""
        result = strategy.calculate(quality=1, ease_factor=2.5, interval=1, repetitions=0)
        assert result.ease_factor < 2.0


class TestSM2Quality0:
    """quality=0: Complete blackout."""

    def test_q0_resets(self, strategy):
        """q=0 resets repetitions and interval."""
        result = strategy.calculate(quality=0, ease_factor=2.5, interval=60, repetitions=15)
        assert result.repetitions == 0
        assert result.interval == 1

    def test_q0_ease_factor_heavily_penalized(self, strategy):
        """q=0 causes largest ease factor decrease."""
        result = strategy.calculate(quality=0, ease_factor=2.5, interval=1, repetitions=0)
        # EF formula: 2.5 + (0.1 - 5*0.08 - 25*0.02) = 2.5 + (0.1 - 0.4 - 0.5) = 2.5 - 0.8 = 1.7
        assert result.ease_factor == pytest.approx(1.7, abs=0.01)

    def test_q0_clamps_ease_factor(self, strategy):
        """q=0 from already-low EF clamps at 1.3."""
        result = strategy.calculate(quality=0, ease_factor=1.3, interval=1, repetitions=0)
        assert result.ease_factor == SM2Strategy.MIN_EASE_FACTOR


class TestSM2InvalidInput:
    """Tests for invalid quality values."""

    def test_quality_negative(self, strategy):
        """Negative quality raises ValueError."""
        with pytest.raises(ValueError, match="Quality must be between 0 and 5"):
            strategy.calculate(quality=-1, ease_factor=2.5, interval=1, repetitions=0)

    def test_quality_too_high(self, strategy):
        """Quality > 5 raises ValueError."""
        with pytest.raises(ValueError, match="Quality must be between 0 and 5"):
            strategy.calculate(quality=6, ease_factor=2.5, interval=1, repetitions=0)


class TestSM2EaseFactorFormula:
    """Verify the exact SM-2 ease factor formula."""

    @pytest.mark.parametrize(
        ("quality", "expected_ef_delta"),
        [
            (5, 0.10),  # 0.1 - 0*(0.08 + 0*0.02) = 0.1
            (4, 0.00),  # 0.1 - 1*(0.08 + 1*0.02) = 0.1 - 0.10 = 0.0
            (3, -0.14),  # 0.1 - 2*(0.08 + 2*0.02) = 0.1 - 0.24 = -0.14
            (2, -0.32),  # 0.1 - 3*(0.08 + 3*0.02) = 0.1 - 0.42 = -0.32
            (1, -0.54),  # 0.1 - 4*(0.08 + 4*0.02) = 0.1 - 0.64 = -0.54
            (0, -0.80),  # 0.1 - 5*(0.08 + 5*0.02) = 0.1 - 0.90 = -0.80
        ],
    )
    def test_ease_factor_delta(self, strategy, quality, expected_ef_delta):
        """Verify ease factor changes match SM-2 formula exactly."""
        result = strategy.calculate(quality=quality, ease_factor=2.5, interval=6, repetitions=2)
        expected = max(SM2Strategy.MIN_EASE_FACTOR, 2.5 + expected_ef_delta)
        assert result.ease_factor == pytest.approx(expected, abs=0.001)


class TestSM2IntervalProgression:
    """Test the interval progression over multiple reviews."""

    def test_perfect_review_chain(self, strategy):
        """Simulate a chain of perfect reviews and verify interval growth."""
        ef = 2.5
        interval = 1
        reps = 0

        # First review
        r = strategy.calculate(quality=5, ease_factor=ef, interval=interval, repetitions=reps)
        assert r.interval == 1
        assert r.repetitions == 1

        # Second review
        r = strategy.calculate(quality=5, ease_factor=r.ease_factor, interval=r.interval, repetitions=r.repetitions)
        assert r.interval == 6
        assert r.repetitions == 2

        # Third review (interval should grow significantly)
        r = strategy.calculate(quality=5, ease_factor=r.ease_factor, interval=r.interval, repetitions=r.repetitions)
        assert r.interval > 6
        assert r.repetitions == 3

    def test_failure_resets_progress(self, strategy):
        """Failing after successful reviews resets to beginning."""
        # Build up to rep=3
        ef = 2.5
        interval = 1
        reps = 0
        for _ in range(3):
            r = strategy.calculate(quality=5, ease_factor=ef, interval=interval, repetitions=reps)
            ef = r.ease_factor
            interval = r.interval
            reps = r.repetitions

        assert reps == 3
        assert interval > 6

        # Now fail with quality=1
        r = strategy.calculate(quality=1, ease_factor=ef, interval=interval, repetitions=reps)
        assert r.repetitions == 0
        assert r.interval == 1


class TestSchedulingResult:
    """Tests for SchedulingResult dataclass."""

    def test_frozen(self):
        """SchedulingResult is immutable."""
        result = SchedulingResult(ease_factor=2.5, interval=1, repetitions=0)
        with pytest.raises(AttributeError):
            result.ease_factor = 3.0  # type: ignore[misc]

    def test_slots(self):
        """SchedulingResult uses __slots__ for memory efficiency."""
        result = SchedulingResult(ease_factor=2.5, interval=1, repetitions=0)
        assert not hasattr(result, "__dict__")

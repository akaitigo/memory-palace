"""Spaced repetition scheduling strategies.

Implements the Strategy pattern to allow future migration from SM-2 to ML-based models.

SM-2 Algorithm Reference: https://super-memory.com/english/ol/sm2.htm
"""

from __future__ import annotations

import abc
from dataclasses import dataclass

# SM-2 quality thresholds and constants
_MAX_QUALITY = 5
_PASS_THRESHOLD = 3
_FIRST_SUCCESS_REPS = 1
_SECOND_SUCCESS_REPS = 2
_FIRST_SUCCESS_INTERVAL = 1
_SECOND_SUCCESS_INTERVAL = 6


@dataclass(frozen=True, slots=True)
class SchedulingResult:
    """Result of a scheduling calculation.

    Attributes:
        ease_factor: Updated ease factor (>= 1.3).
        interval: Next review interval in days.
        repetitions: Updated consecutive correct answer count.
    """

    ease_factor: float
    interval: int
    repetitions: int


class SchedulingStrategy(abc.ABC):
    """Abstract base class for spaced repetition scheduling strategies."""

    @abc.abstractmethod
    def calculate(
        self,
        quality: int,
        ease_factor: float,
        interval: int,
        repetitions: int,
    ) -> SchedulingResult:
        """Calculate the next scheduling parameters after a review.

        Args:
            quality: Self-assessment score (0-5).
            ease_factor: Current ease factor.
            interval: Current review interval in days.
            repetitions: Current count of consecutive correct answers.

        Returns:
            Updated scheduling parameters.
        """


class SM2Strategy(SchedulingStrategy):
    """SM-2 (SuperMemo 2) spaced repetition scheduling strategy.

    Rules:
        - quality < 3: Reset repetitions to 0, interval to 1 (re-learn).
        - quality >= 3: Increment repetitions, scale interval by ease_factor.
        - ease_factor is updated based on quality and clamped to minimum 1.3.
        - First successful review: interval = 1.
        - Second successful review: interval = 6.
        - Subsequent successful reviews: interval = round(interval * ease_factor).
    """

    MIN_EASE_FACTOR = 1.3

    def calculate(
        self,
        quality: int,
        ease_factor: float,
        interval: int,
        repetitions: int,
    ) -> SchedulingResult:
        """Calculate next SM-2 scheduling parameters.

        Args:
            quality: Self-assessment score (0-5).
            ease_factor: Current ease factor (>= 1.3).
            interval: Current review interval in days.
            repetitions: Current consecutive correct answer count.

        Returns:
            Updated scheduling parameters.

        Raises:
            ValueError: If quality is not in range 0-5.
        """
        if not (0 <= quality <= _MAX_QUALITY):
            msg = f"Quality must be between 0 and {_MAX_QUALITY}, got {quality}"
            raise ValueError(msg)

        # Update ease factor using the SM-2 formula
        new_ease_factor = ease_factor + (0.1 - (_MAX_QUALITY - quality) * (0.08 + (_MAX_QUALITY - quality) * 0.02))
        new_ease_factor = max(self.MIN_EASE_FACTOR, new_ease_factor)

        if quality < _PASS_THRESHOLD:
            # Failed recall: reset to re-learn
            return SchedulingResult(
                ease_factor=new_ease_factor,
                interval=1,
                repetitions=0,
            )

        # Successful recall: advance
        new_repetitions = repetitions + 1

        if new_repetitions == _FIRST_SUCCESS_REPS:
            new_interval = _FIRST_SUCCESS_INTERVAL
        elif new_repetitions == _SECOND_SUCCESS_REPS:
            new_interval = _SECOND_SUCCESS_INTERVAL
        else:
            new_interval = round(interval * new_ease_factor)

        return SchedulingResult(
            ease_factor=new_ease_factor,
            interval=new_interval,
            repetitions=new_repetitions,
        )

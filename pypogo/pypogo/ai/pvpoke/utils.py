import random
from typing import List, Optional

from .constants import DecisionOption


def choose_option(
    options: List[DecisionOption], rng: Optional[random.Random] = None
) -> DecisionOption:
    """
    Randomly selects an option from a list of decision options based on their weights.

    Args:
        options (List[DecisionOption]): A list of decision options.
        rng (random.Random, optional): Stream to draw from. Callers pass their
            own so a decision is reproducible; the global RNG is the default
            only so existing callers keep working, and an AI should not use it.

    Returns:
        DecisionOption: The selected decision option.
    """
    option_bucket = [option for option in options for _ in range(option.weight)]

    if len(option_bucket) == 0:
        option_bucket.append(options[0])

    return (rng or random).choice(option_bucket)

import random
from typing import List

from .constants import DecisionOption


def choose_option(options: List[DecisionOption]) -> DecisionOption:
    """
    Randomly selects an option from a list of decision options based on their weights.

    Args:
        options (List[DecisionOption]): A list of decision options.

    Returns:
        DecisionOption: The selected decision option.
    """
    option_bucket = [option for option in options for _ in range(option.weight)]

    if len(option_bucket) == 0:
        option_bucket.append(options[0])

    return random.choice(option_bucket)

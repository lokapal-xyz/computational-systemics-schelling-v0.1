"""One Operational Status entry on an agent.

Fronterization is the current attribute value.
Permeability is the tolerance threshold for that value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class StatusEntry:
    """A single criterion carried by an agent.

    Attributes:
        criterion: Name of the attribute being compared, for example "type".
        fronterization: Current value of that attribute. v0.1 uses 0 or 1.
        permeability: Fraction of similar neighbors required, in [0.0, 1.0].
            Receptivity fires when local similarity is strictly below this.
        mutable: Whether fronterization may change later. v0.1 leaves this
            False and does not update the value.
    """

    criterion: str
    fronterization: Any
    permeability: float
    mutable: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.criterion, str) or not self.criterion:
            raise ValueError("criterion must be a non-empty string")
        if isinstance(self.permeability, bool) or not isinstance(
            self.permeability, (int, float)
        ):
            raise TypeError("permeability must be a number in [0, 1]")
        self.permeability = float(self.permeability)
        if not 0.0 <= self.permeability <= 1.0:
            raise ValueError("permeability must be in [0, 1]")

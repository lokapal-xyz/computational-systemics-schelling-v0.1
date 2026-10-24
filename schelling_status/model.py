"""Schelling model driven by Operational Status.

Each step activates agents in random order. An agent may carry any number
of StatusEntry objects. v0.1 gives every agent one binary entry.
"""

from __future__ import annotations

import numbers

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import Cell, OrthogonalMooreGrid

from schelling_status.agent import SchellingAgent
from schelling_status.status import StatusEntry


class SchellingModel(Model):
    """Grid of agents with binary Fronterization and a shared Permeability.

    Defaults follow the v0.1 spec: 50×50, vacancy 0.15, two equal groups,
    Moore neighborhood, non-toroidal, permeability 0.4, up to 150 steps.

    The constructor is keyword-only. The dashboard aliases are `width`,
    `height`, `density` (1 − vacancy rate), and `minority_fraction`
    (share of Fronterization B, value 1). Omit `minority_fraction` for
    equal groups.

    Logged after each step, and once for the initial grid (step 0):

    - dissatisfied: agents whose Receptivity currently fires
    - moves: agents who relocated during that step (0 at step 0)
    - segregation_index: mean local similarity across defined ratios

    The run stops early when dissatisfied reaches 0. That is a fixed point:
    with vacancies, it is also the step where moves fall to 0.
    """

    def __init__(
        self,
        *,
        grid_width: int | None = None,
        grid_height: int | None = None,
        width: int | None = None,
        height: int | None = None,
        vacancy_rate: float | None = None,
        density: float | None = None,
        permeability: float = 0.4,
        n_types: int = 2,
        minority_fraction: float | None = None,
        steps: int = 150,
        seed: int | str | None = None,
        criterion: str = "type",
    ) -> None:
        """Build a random grid and record the initial metrics.

        Args:
            grid_width: Cells along x. CLI name. Default 50.
            grid_height: Cells along y. CLI name. Default 50.
            width: Dashboard name for grid_width.
            height: Dashboard name for grid_height.
            vacancy_rate: Fraction of cells left empty, in [0, 1). Default 0.15.
            density: Fraction of cells occupied, in (0, 1]. Dashboard name.
            permeability: Shared tolerance threshold, in [0, 1].
            n_types: Number of fronterization values when minority_fraction
                is omitted. v0.1 uses 2.
            minority_fraction: Share of agents with Fronterization B (value 1).
                The rest are Fronterization A (value 0).
            steps: Maximum sweeps for the CLI runner. The dashboard plays
                until nobody is dissatisfied.
            seed: RNG seed. Integers and numeric strings are accepted.
                None draws a fresh seed.
            criterion: StatusEntry criterion name. v0.1 uses "type".
        """
        super().__init__(rng=_coerce_seed(seed))
        self.grid_width = _positive_int(
            "width", _one_of("width", width, "grid_width", grid_width, 50)
        )
        self.grid_height = _positive_int(
            "height", _one_of("height", height, "grid_height", grid_height, 50)
        )
        self.density, self.vacancy_rate = _density_and_vacancy(density, vacancy_rate)
        self.permeability = _unit_interval("permeability", permeability, upper_inclusive=True)
        self.n_types = _positive_int("n_types", n_types)
        if minority_fraction is None:
            self.minority_fraction = None
        else:
            self.minority_fraction = _unit_interval(
                "minority_fraction", minority_fraction, upper_inclusive=True
            )
        self.max_steps = _positive_int("steps", steps)
        self.criterion = criterion

        self.grid = OrthogonalMooreGrid(
            (self.grid_width, self.grid_height),
            torus=False,
            capacity=1,
            random=self.random,
        )
        self._place_agents()

        self.moves = 0
        self.dissatisfied = 0
        self.segregation_index = 0.0
        self.datacollector = DataCollector(
            model_reporters={
                "dissatisfied": "dissatisfied",
                "moves": "moves",
                "segregation_index": "segregation_index",
            }
        )
        self._record_state()

    def _place_agents(self) -> None:
        """Fill the grid at the vacancy rate.

        Equal groups when minority_fraction is omitted. Otherwise value 1
        (Fronterization B) is that share, and value 0 (Fronterization A)
        is the rest.
        """
        n_cells = self.grid_width * self.grid_height
        n_agents = round(n_cells * (1.0 - self.vacancy_rate))
        if n_agents < 1:
            raise ValueError("vacancy_rate leaves no agents on the grid")
        if n_agents > n_cells:
            raise ValueError("agent count exceeds the number of cells")

        cells = list(self.grid.all_cells)
        chosen = self.random.sample(cells, n_agents)
        # Fronterization A is 0. Fronterization B is 1, the minority when
        # minority_fraction is set. Equal groups keep the original v0.1 split.
        if self.minority_fraction is None:
            values = _balanced_values(n_agents, self.n_types)
        else:
            n_minority = round(n_agents * self.minority_fraction)
            n_minority = min(max(n_minority, 0), n_agents)
            values = [1] * n_minority + [0] * (n_agents - n_minority)
        self.random.shuffle(values)

        for cell, value in zip(chosen, values):
            entry = StatusEntry(
                criterion=self.criterion,
                fronterization=value,
                permeability=self.permeability,
                mutable=False,
            )
            # The list is length 1 in v0.1. The agent stores it as a list.
            SchellingAgent(self, cell, [entry])

    def random_empty_cell(self) -> Cell | None:
        """Return a random empty cell, or None when the grid is full."""
        try:
            cell = self.grid.select_random_empty_cell()
        except IndexError:
            return None
        if not cell.is_empty:
            return None
        return cell

    def mean_local_similarity(self) -> float:
        """Segregation index: mean of every defined local-similarity ratio.

        Agents with no occupied neighbors contribute nothing, because their
        ratio is undefined. With one status entry this is the mean similarity
        of agents who have at least one neighbor. Returns 0.0 when no agent
        has a defined ratio.
        """
        ratios: list[float] = []
        for agent in self.agents:
            ratios.extend(agent.similarity_ratios())
        if not ratios:
            return 0.0
        return sum(ratios) / len(ratios)

    def count_dissatisfied(self) -> int:
        """Agents for whom Receptivity currently fires."""
        return sum(1 for agent in self.agents if agent.receptivity())

    def fronterization_grid(self, criterion: str | None = None) -> list[list[object]]:
        """Final configuration as rows of fronterization values.

        Row index is y, column index is x. An empty cell is None.
        """
        criterion = self.criterion if criterion is None else criterion
        grid: list[list[object]] = [
            [None for _ in range(self.grid_width)] for _ in range(self.grid_height)
        ]
        for agent in self.agents:
            x, y = agent.position
            grid[y][x] = agent.fronterization_on(criterion)
        return grid

    def _record_state(self) -> None:
        """Snapshot dissatisfied and the segregation index, then store the row."""
        self.dissatisfied = self.count_dissatisfied()
        self.segregation_index = self.mean_local_similarity()
        self.datacollector.collect(self)
        if self.dissatisfied == 0:
            self.running = False

    def step(self) -> None:
        """Run one random-sequential sweep and log the resulting grid.

        The loop body is `activate` on each agent. That method walks the
        status list, so a second StatusEntry does not change this step.
        """
        self.moves = 0
        self.agents.shuffle_do("activate")
        self._record_state()


def _one_of(name_a: str, value_a, name_b: str, value_b, default):
    """Return the single provided alias, or the default when both are absent."""
    if value_a is not None and value_b is not None:
        raise ValueError(f"pass {name_a} or {name_b}, not both")
    if value_a is not None:
        return value_a
    if value_b is not None:
        return value_b
    return default


def _density_and_vacancy(
    density: float | None, vacancy_rate: float | None
) -> tuple[float, float]:
    """Resolve occupancy. Density is the share of filled cells."""
    if density is not None and vacancy_rate is not None:
        raise ValueError("pass density or vacancy_rate, not both")
    if density is not None:
        density = _unit_interval("density", density, upper_inclusive=True)
        if density <= 0.0:
            raise ValueError("density must be in (0, 1]")
        return density, 1.0 - density
    if vacancy_rate is None:
        vacancy_rate = 0.15
    vacancy_rate = _unit_interval("vacancy_rate", vacancy_rate, upper_inclusive=False)
    return 1.0 - vacancy_rate, vacancy_rate


def _coerce_seed(value: int | str | None) -> int | None:
    """Accept an int seed or the numeric string Solara's text input produces."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("seed must be an integer")
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return None
        try:
            return int(text)
        except ValueError as exc:
            raise ValueError("seed must be an integer") from exc
    if isinstance(value, numbers.Integral):
        return int(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    raise TypeError("seed must be an integer")


def _positive_int(name: str, value: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer >= 1")
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, numbers.Integral) and not isinstance(value, int):
        value = int(value)
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be an integer >= 1")
    return value


def _unit_interval(name: str, value: float, *, upper_inclusive: bool) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number")
    value = float(value)
    too_high = value > 1.0 if upper_inclusive else value >= 1.0
    if value < 0.0 or too_high:
        bound = "[0, 1]" if upper_inclusive else "[0, 1)"
        raise ValueError(f"{name} must be in {bound}")
    return value


def _balanced_values(n_agents: int, n_types: int) -> list[int]:
    """Split agents into groups as equal as the count allows."""
    base, extra = divmod(n_agents, n_types)
    values: list[int] = []
    for type_id in range(n_types):
        count = base + (1 if type_id < extra else 0)
        values.extend([type_id] * count)
    return values

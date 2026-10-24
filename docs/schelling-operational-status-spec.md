# Schelling Operational Status — Implementation Spec (v0.1)

**Purpose:** Concrete design for the first Computational Systemics prototype.  
**Companion document:** `computational-systemics-summary.md` (rationale and framing).  
**Target:** Minimal runnable model that implements the refined Operational Status mapping on a Schelling base.

## 1. Goal of v0.1

A grid-based agent model in which:

- Each agent has one or more **status entries**.
- Each entry has a **Fronterization** (current attribute value) and a **Permeability** (tolerance threshold).
- **Receptivity** checks whether the local neighborhood violates the threshold.
- **Proceptivity** moves the agent to a random empty cell if the threshold is breached.
- The model produces the classic Schelling clustering dynamic when Fronterization is binary and fixed, and remains interpretable when Fronterization can change or when multiple criteria are present.

Out of scope for v0.1: status updating rules, relevance weights, multi-axis interaction beyond independent checks, visualization polish, parameter sweeps.

## 2. Agent Schema

```text
Agent
├── id: int
├── position: (x, y)
├── statuses: list[StatusEntry]
└── (optional) color / label for visualization

StatusEntry
├── criterion: str          # e.g. "type", "income", "religion"
├── fronterization: any     # current value (int, float, str, category)
├── permeability: float     # tolerance threshold in [0.0, 1.0]
│                           # fraction of similar neighbors required
└── mutable: bool           # whether fronterization may change later
```

For the first runnable version use a single StatusEntry per agent with `criterion = "type"` and binary fronterization (0 or 1). The schema already supports an array so multi-criterion can be added without structural change.

## 3. Grid and Neighborhood

- 2-D grid (toroidal or non-toroidal; non-toroidal is fine for v0.1).
- Occupancy: agents + empty cells (vacancy rate as a parameter, default 0.1–0.2).
- Neighborhood: Moore (8 adjacent cells) or von Neumann (4). Default to Moore.
- “Similar” on a criterion: exact match of fronterization values (for binary/categorical). For continuous fronterization (later), define a similarity window.

## 4. Step Loop (plain language)

Each step (or each agent activation):

1. For every StatusEntry of the agent:
   - Count neighbors.
   - Count how many have matching fronterization on that criterion.
   - Compute local similarity ratio = matching / total neighbors (ignore empty cells or treat as non-matching; choose one and document it).
2. Receptivity: if similarity ratio < permeability for any StatusEntry, the agent is dissatisfied.
3. Proceptivity: if dissatisfied, move to a randomly chosen empty cell (or stay if no empty cell exists).
4. (Optional later) Update mutable fronterization values according to a separate rule.

Agents can be activated in random order each full sweep, or simultaneously with conflict resolution. Random sequential is simplest for v0.1.

## 5. Initial Parameters (v0.1 defaults)

| Parameter              | Default   | Notes                                      |
|------------------------|-----------|--------------------------------------------|
| grid_width             | 50        |                                            |
| grid_height            | 50        |                                            |
| vacancy_rate           | 0.15      |                                            |
| n_agents               | derived   | grid_size * (1 - vacancy_rate)             |
| n_types                | 2         | binary fronterization                      |
| permeability           | 0.3–0.5   | classic Schelling range; make it a param   |
| neighborhood           | Moore     |                                            |
| steps                  | 100–200   | or until no moves                          |
| seed                   | optional  | for reproducibility                        |

## 6. Observables / Logging

Per step (or at intervals):

- Number of dissatisfied agents
- Number of moves
- Segregation index (e.g., average local similarity ratio across agents)
- Optional: simple visualization of the grid colored by fronterization

Store final configuration and time series so results can be compared across permeability values.

## 7. Success Criteria for v0.1

- Runs without error on the default parameters.
- With permeability ≈ 0.3 and two equal groups, visible clustering emerges (classic Schelling behavior).
- Changing permeability changes the degree of clustering in the expected direction.
- Code structure allows adding a second StatusEntry without rewriting the step loop.
- Mapping from Conciliatorics terms (Fronterization, Permeability, Receptivity, Proceptivity) to code is documented in comments or a short README section.

## 8. Suggested Implementation Order

1. Single-criterion binary agents + fixed permeability → recover Schelling.
2. Parameterize permeability and vacancy rate.
3. Refactor so statuses are a list (even if length 1).
4. Add logging and a basic plot or print summary.
5. (Next) Allow fronterization to be updated by an external rule and re-check thresholds.

## 9. Technology Notes

- Preferred: Mesa (Python) for data collection and later analysis.
- Acceptable alternative: NetLogo for fastest visual prototype.
- Keep the status-to-behavior mapping explicit so the Computational Systemics framing remains visible in the code.

## 10. Explicitly Deferred

- Dynamic fronterization update rules
- Multi-criterion interaction (beyond independent checks)
- Relevance / resistance weights
- Hypo/Hyper vs Sub/Supra gradations
- Iteration / conciliation pathway mechanics
- YAML config loading (can be added once the core runs)

---

*This spec is the implementation companion to `computational-systemics-summary.md`. Feed both to Grok Build; treat this file as the primary coding reference for v0.1.*

# AGENTS.md — Computational Systemics

Instructions for AI coding agents (including Grok Build) working in this repository.

## Project Purpose

This repository implements **Computational Systemics**: generative agent-based models grounded in the Conciliatorics framework. The first prototype is a Schelling-style segregation model whose tolerance and movement rules are expressed through Operational Status (Fronterization, Permeability, Receptivity, Proceptivity).

The goal is a clean, interpretable model that recovers classic Schelling behavior while remaining extensible to multi-criterion statuses and later Conciliatorics principles.

## Key Documents

All conceptual and design material lives in `./docs/`:

- `docs/schelling-operational-status-spec.md` — v0.1 model spec (agent schema, step loop, parameters, success criteria). **Primary coding reference for the model.**
- `docs/visualization-spec.md` — Dashboard contract (layout, colors, stats, chart, controls). **Primary coding reference for `app.py`.**
- `docs/computational-systemics-summary.md` — Why this implementation exists, and the refined Operational Status mapping.
- `docs/conciliatorics.md` — The full Conciliatorics treatise. Source of the Operational Status operators.

Read the spec that matches the task. Consult the summary for framing. Open the treatise only when a term or operator needs its original definition. `README.md` is the map of the current tree, the run commands, and the defaults.

## Current tree

v0.1 is already implemented. Extend these files. Do not add a second model package or a new entry point unless the user asks.

- `schelling_status/` — the model. `status.py` (`StatusEntry`), `agent.py` (`SchellingAgent`), `model.py` (`SchellingModel`).
- `run.py` — CLI step log. Defaults: 50×50, vacancy 0.15, two equal groups, permeability 0.4, 150 steps, seed 1. The step cap is enforced here, not inside `SchellingModel.step()`.
- `app.py` — Solara dashboard. Defaults differ from the CLI: 40×40, density 0.75, permeability 0.40, Fronterization B share 0.30, seed 42, play interval 200 ms. Leave the CLI defaults alone when changing the dashboard.
- `requirements.txt` — `mesa[viz]==3.5.1` and NetworkX. Mesa imports NetworkX at startup. The viz extra supplies Solara and Matplotlib. Mesa 3.5 requires Python >=3.12.
- `setup.sh` — creates `.venv` when missing, installs `requirements.txt` when packages are missing or outdated, and runs `solara run app.py`. The manual quick start in `README.md` stays.

`SchellingModel.step()` zeroes the move count, calls `agents.shuffle_do("activate")`, and records the step. A second `StatusEntry` must be possible without rewriting that method. Receptivity already walks `statuses`.

## v0.1 rules

Keep the behavior the spec describes:

- Grid with vacancies. Empty cells are left out of the similarity ratio. No occupied neighbors means the ratio is undefined and the agent is satisfied.
- Agents carry a list of `StatusEntry` objects. v0.1 uses one entry: `criterion = "type"`, fronterization `0` or `1`, `mutable=False`.
- Fronterization is the current attribute value. Permeability is the tolerance threshold in `[0, 1]`.
- Receptivity fires when local similarity is strictly below permeability for any entry.
- Proceptivity moves the agent to a random empty cell when Receptivity fires, or leaves it in place if none exists.
- Binary fronterization and permeability around 0.3–0.5 recover classic Schelling clustering.
- Each step logs dissatisfied agents, moves, and the segregation index (the mean of defined local-similarity ratios).
- The run stops when no agent is dissatisfied. `run.py` also stops at its step cap.

The constructor is keyword-only. Passing both `width` and `grid_width`, or both `density` and `vacancy_rate`, raises.

## Coding conventions

- Prefer Mesa (Python) unless the user requests NetLogo.
- This repository uses a local virtual environment at `.venv`. Before any Python command, install, or run:
```bash
source .venv/bin/activate
```
- Install from `requirements.txt`. `pip install mesa` omits Solara, Matplotlib, and NetworkX, and `solara run app.py` will not start.
- Keep the Operational Status mapping explicit in the code and in `README.md`.
- Make parameters easy to change.
- Prefer clarity over premature optimization.
- The dashboard draws with Matplotlib through `SpaceRenderer`. `StatusSpaceRenderer` calls `setup_structure` and `setup_agents`. Controls live in `solara.Sidebar`. The main pane is `solara.Columns([13, 7])`: the grid, then the stats and chart. Do not move those components into `SolaraViz`: its `GridDraggable` never mounts on this Solara build, because vue-grid-layout calls `window.Vue.use` and that function is absent. The stats panel is one HTML widget updated in place. `solara.Markdown` builds a new widget every step, the text vanishes for a frame, and the chart jumps.
- Play is Mesa's `ModelController` in the sidebar. The dashboard is local. The Svelte site links to this repository and does not embed the model. Do not add a hosted Solara target.

## Workflow

1. Read the matching spec before changing model behavior or the dashboard.
2. Change the current tree. The binary one-entry model and the dashboard are already there.
3. Verify model changes with `python run.py`. Verify dashboard changes with `solara run app.py` and confirm the grid, the stats, and the chart actually render.
4. Ask before adding anything listed as deferred.

## Out of scope unless requested

- Dynamic fronterization updates, relevance weights, Hypo/Hyper and Sub/Supra gradations.
- Multi-criterion interaction beyond the independent per-entry check.
- YAML config and parameter sweeps.
- Full Conciliatorics machinery beyond Operational Status.
- Political or real-world case data.
- A public hosted dashboard (PyCafe, Render, Hugging Face, or another Solara host).

When in doubt, stay inside the spec and keep the Operational Status mapping visible in the code.

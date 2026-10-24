# Visualization Spec — Schelling Operational Status Model

**Target:** Interactive browser dashboard for the v0.1 Schelling Operational Status prototype.  
**Use cases:** Live streams, website demos, build-in-public posts.  
**Aesthetic goal:** Clean, precise, and intriguing — not flashy. Viewers should immediately see clustering emerge and understand the Operational Status mapping.

## Technology

- **Mesa 3.5.1** with Solara (`pip install -r requirements.txt`). Mesa 3.5 requires Python >=3.12. `.python-version` pins 3.12.
- Backend: **matplotlib** via `SpaceRenderer`.
- Launch: `solara run app.py` → open the local URL in a browser. The public showcase is the Render web service in `render.yaml`.
- Model constructor must accept **keyword-only arguments** (`ModelCreator` checks this).

## Layout

Single-page dashboard with three regions:

1. **Sidebar** — Controls, model parameters, and the step log. `solara.Sidebar`.
2. **Main, left** — Live grid. `solara.Columns([13, 7])` gives this about 65% of the page.
3. **Main, right** — Live stats, then the segregation index chart.

Use a dark or near-black background with high-contrast agent colors so the grid reads clearly on stream overlays and screenshots.

## Grid Portrayal

Agents are circles (or slightly rounded squares) on a square grid with vacancies shown as empty cells.

**Color by Fronterization** (binary case for v0.1):

- Fronterization A → `#4FC3F7` (clear cyan)
- Fronterization B → `#FFB74D` (warm amber)

**Edge / state cue** (optional but recommended):

- Dissatisfied agent (Receptivity triggered, about to move or just moved): thin white or light-gray stroke.
- Satisfied agent: no stroke or very subtle dark stroke.

**Size:** Uniform, large enough to be readable at stream resolution (≈40–60 px markers on a 40×40 or 50×50 grid).

**Grid background:** Dark gray (`#1E1E1E` or similar) with faint cell borders so vacancies remain visible.

**Tooltip (on hover):**  
`ID | Fronterization: A | Permeability: 0.40 | Satisfied: yes`

Keep the mapping explicit in the legend:

```
Cyan  = Fronterization A
Amber = Fronterization B
White edge = currently dissatisfied
```

## Live Stats Panel

Always visible, updated every step:

- **Step**
- **Segregation index** (current value, 3 decimals)
- **Dissatisfied agents** (count and % of occupied cells)
- **Total moves** (cumulative)
- **Permeability** (current parameter)

Optional small status line:  
`Stopped: all agents satisfied` or `Running…`

## Chart

Line chart of **segregation index** over steps.

- Color: same cyan or a neutral white/light gray.
- Y-axis: 0.4 – 1.0 (or auto-scale with a sensible floor).
- Title: “Segregation Index”
- No legend clutter; single series.

## Controls

Standard SolaraViz controls plus these model parameters as sliders:

| Parameter              | Type   | Range        | Default | Notes                          |
|------------------------|--------|--------------|---------|--------------------------------|
| `width` / `height`     | int    | 20–60        | 40      | Keep square for simplicity     |
| `density`              | float  | 0.5–0.95     | 0.75    |                                |
| `permeability`         | float  | 0.1–0.8      | 0.40    | The key tolerance threshold    |
| `minority_fraction`    | float  | 0.1–0.5      | 0.30    | Share of Fronterization B      |
| `seed`                 | int    | —            | 42      | For reproducibility            |

Play / Pause / Step / Reset come from Mesa's `ModelController`.  
Play interval: 150–250 ms so the process is readable on stream. The dashboard default is 200 ms.

## Code Structure Expectations

- `app.py` — Solara entry point (this is what `solara run` targets).
- Reuse existing model classes; do not rewrite the step loop.
- `agent_portrayal(agent)` returns an `AgentPortrayalStyle`.
- `StatusSpaceRenderer` calls `setup_structure` and `setup_agents`, and sets `post_process` to the dark grid style.
- `make_plot_component` for the segregation index.
- Play controls are Mesa's `ModelController` in the sidebar.
- Optional custom `@solara.component` for the stats panel if the built-in text helpers are insufficient.
- All model instantiation uses keyword arguments only.

## Visual Polish (keep modest)

- Consistent padding and spacing.
- Title at top: **Computational Systemics — Schelling Operational Status**
- Small subtitle: “Fronterization · Permeability · Receptivity · Proceptivity”
- No gradients, animations, or particle effects.
- High contrast, readable at 1080p stream resolution.
- Optional: faint watermark or footer with “v0.1 prototype”.

## Success Criteria

- Grid updates live and shows clear clustering as the model runs.
- Stats and chart update every step.
- Parameter changes via sliders recreate the model cleanly.
- Screenshot of a mid-run or final state looks intentional and professional.
- Runs without console errors under the existing `.venv`.

## Out of Scope for This Spec

- Multi-criterion color encoding (defer until second StatusEntry is active).
- Dynamic Fronterization color changes.
- 3D, network layouts, or custom JavaScript canvases.
- Export-to-video automation (can be added later if needed for streams).

## Implementation Notes for Grok Build

1. Confirm Mesa version ≥ 3.5 and that `mesa[viz]` (solara + matplotlib) is available in `.venv`.
2. Inspect the existing model’s agent attributes (especially how Fronterization and satisfaction/dissatisfaction are stored) before writing the portrayal function.
3. Prefer `AgentPortrayalStyle` over raw dicts.
4. Test with a short run (20–30 steps) and a full run to equilibrium.
5. Keep the portrayal function simple and well-commented so the Operational Status → visual mapping stays obvious.

Once this dashboard is running, the prototype is ready to show. Subsequent work can layer multi-criterion coloring or dynamic status updates on top of the same visualization structure.

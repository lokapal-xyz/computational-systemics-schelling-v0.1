"""Interactive dashboard for the Schelling Operational Status model.

Launch from the repository root:

    solara run app.py

Operational Status → visual mapping (binary v0.1):

- Fronterization A (value 0) → cyan marker
- Fronterization B (value 1) → amber marker
- Receptivity firing (dissatisfied) → white edge
- Satisfied → faint dark edge
- Permeability is the slider that sets every entry's threshold
- Proceptivity is the move that plays out on the grid

Matplotlib draws the grid to a PNG, so a hover tooltip cannot be attached.
The same fields are listed in the side panel.

The main pane is a Solara column layout. SolaraViz would place the grid,
stats, and chart in ``solara.GridDraggable``. That widget's vue-grid-layout
bundle calls ``window.Vue.use``, which this Solara build does not provide,
so those components never mount. Play, the sliders, and the renderer are
still Mesa's.
"""

from __future__ import annotations

import solara
import solara.lab
from mesa.visualization import Slider, SpaceRenderer, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle
from mesa.visualization.solara_viz import (
    ModelController,
    ModelCreator,
    ShowSteps,
    SpaceRendererComponent,
)
from mesa.visualization.utils import update_counter

from schelling_status import SchellingModel

# Near-black field so vacancies stay visible and the two groups read on a stream.
GRID_BACKGROUND = "#1E1E1E"
PAGE_BACKGROUND = "#121212"
GRID_LINE = "#3A3A3A"
COLOR_A = "#4FC3F7"
COLOR_B = "#FFB74D"
EDGE_DISSATISFIED = "#F5F5F5"
EDGE_SATISFIED = "#2A2A2A"
CHART_COLOR = "#4FC3F7"
FIGURE_INCHES = 8.0

solara.lab.theme.dark = True


def _marker_area(span: int) -> float:
    """Scatter area that fills most of one cell on an 8-inch figure."""
    cell_points = FIGURE_INCHES * 72.0 / max(span, 1)
    return (0.72 * cell_points) ** 2


def agent_portrayal(agent) -> AgentPortrayalStyle:
    """Draw one agent from its Fronterization and current Receptivity.

    The first status entry is the binary type used in v0.1. A later entry
    does not change this function's shape; multi-criterion color is deferred.
    """
    entry = agent.statuses[0]
    if entry.fronterization == 0:
        color = COLOR_A
    elif entry.fronterization == 1:
        color = COLOR_B
    else:
        color = "#BDBDBD"
    dissatisfied = agent.receptivity()
    span = max(agent.model.grid_width, agent.model.grid_height)
    return AgentPortrayalStyle(
        x=agent.cell.coordinate[0],
        y=agent.cell.coordinate[1],
        color=color,
        marker="o",
        size=_marker_area(span),
        edgecolors=EDGE_DISSATISFIED if dissatisfied else EDGE_SATISFIED,
        linewidths=1.4 if dissatisfied else 0.4,
        zorder=3 if dissatisfied else 2,
        alpha=1.0,
    )


def style_grid(ax) -> None:
    """Dark square field. Vacancies are the empty cells between faint borders."""
    figure = ax.get_figure()
    figure.set_size_inches(FIGURE_INCHES, FIGURE_INCHES)
    figure.set_dpi(110)
    figure.patch.set_facecolor(PAGE_BACKGROUND)
    ax.set_facecolor(GRID_BACKGROUND)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#2A2A2A")


def style_segregation_chart(ax) -> None:
    """Single cyan series titled Segregation Index. Floor at 0.4."""
    legend = ax.get_legend()
    if legend is not None:
        legend.remove()
    lines = ax.get_lines()
    low = 0.4
    last_step = 0.0
    if lines:
        ys = lines[0].get_ydata()
        xs = lines[0].get_xdata()
        if len(ys):
            low = min(0.4, float(min(ys)) - 0.05)
        if len(xs):
            last_step = float(max(xs))
    # One point at step 0 otherwise zooms the axis to a fraction of a step.
    ax.set_xlim(-0.5, max(last_step, 1.0))
    ax.set_ylim(low, 1.0)
    ax.ticklabel_format(axis="x", useOffset=False, style="plain")
    ax.set_title("Segregation Index", color="#E8E8E8", fontsize=12)
    ax.set_ylabel("")
    figure = ax.get_figure()
    figure.patch.set_facecolor(PAGE_BACKGROUND)
    figure.set_size_inches(7.2, 2.6)
    ax.set_facecolor(GRID_BACKGROUND)
    ax.tick_params(colors="#C8C8C8")
    ax.xaxis.label.set_color("#C8C8C8")
    ax.title.set_color("#E8E8E8")
    for spine in ax.spines.values():
        spine.set_color("#3A3A3A")


class StatusSpaceRenderer(SpaceRenderer):
    """Moore grid renderer with the Operational Status palette.

    Rebuilt on Reset via ``type(renderer)(model, backend)``, so the grid
    line style is applied again for the new model.
    """

    def __init__(self, model, backend: str = "matplotlib") -> None:
        super().__init__(model, backend=backend)
        self.setup_structure(
            color=GRID_LINE,
            linestyle="-",
            linewidth=0.5,
            alpha=0.95,
        )
        self.setup_agents(agent_portrayal)
        self.post_process = style_grid


def _stats_html(model: SchellingModel) -> str:
    occupied = len(model.agents)
    share = (100.0 * model.dissatisfied / occupied) if occupied else 0.0
    total_moves = int(model.datacollector.get_model_vars_dataframe()["moves"].sum())
    state = "Stopped: all agents satisfied" if not model.running else "Running…"
    row = "margin: 0.55rem 0;"
    return (
        "<div>"
        '<div style="font-weight:600;margin-bottom:0.9rem;">'
        "Fronterization · Permeability · Receptivity · Proceptivity"
        "</div>"
        f'<div style="{row}"><b>Step</b> {model.steps}</div>'
        f'<div style="{row}"><b>Segregation index</b> {model.segregation_index:.3f}</div>'
        f'<div style="{row}"><b>Dissatisfied agents</b> {model.dissatisfied} '
        f"({share:.1f}% of occupied cells)</div>"
        f'<div style="{row}"><b>Total moves</b> {total_moves}</div>'
        f'<div style="{row}"><b>Permeability</b> {model.permeability:.2f}</div>'
        f'<div style="{row}">{state}</div>'
        f'<div style="{row}"><span style="color:{COLOR_A}">●</span> Cyan = Fronterization A</div>'
        f'<div style="{row}"><span style="color:{COLOR_B}">●</span> Amber = Fronterization B</div>'
        f'<div style="{row}"><span style="color:{EDGE_DISSATISFIED}">○</span> '
        "White edge = currently dissatisfied</div>"
        '<div style="margin-top:0.9rem;">v0.1 prototype</div>'
        "</div>"
    )


# Dashboard defaults. The CLI keeps the original 50×50 / vacancy 0.15 model.
DASHBOARD = {
    "width": 40,
    "height": 40,
    "density": 0.75,
    "permeability": 0.40,
    "minority_fraction": 0.30,
    "seed": 42,
}

model_params = {
    "width": Slider("Width", DASHBOARD["width"], 20, 60, 1),
    "height": Slider("Height", DASHBOARD["height"], 20, 60, 1),
    "density": Slider("Density", DASHBOARD["density"], 0.5, 0.95, 0.05),
    "permeability": Slider("Permeability", DASHBOARD["permeability"], 0.1, 0.8, 0.05),
    "minority_fraction": Slider(
        "Fronterization B share",
        DASHBOARD["minority_fraction"],
        0.1,
        0.5,
        0.05,
    ),
    "seed": {
        "type": "InputText",
        "value": DASHBOARD["seed"],
        "label": "Seed",
    },
}

@solara.component
def status_panel(model: SchellingModel):
    """Live counts and the Fronterization / Receptivity legend.

    The text is one HTML widget whose body is replaced in place. solara.Markdown
    builds a new Vue widget whenever the string changes, and that remount leaves
    a blank frame so the chart below jumps to the top.
    """
    update_counter.get()
    return solara.HTML(unsafe_innerHTML=_stats_html(model))


segregation_plot = make_plot_component(
    {"segregation_index": CHART_COLOR},
    post_process=style_segregation_chart,
)

model = SchellingModel(**DASHBOARD)
renderer = StatusSpaceRenderer(model, backend="matplotlib")
renderer.render()
_plot_component, _plot_page = segregation_plot


@solara.component
def page():
    """Dashboard: controls in the sidebar, grid beside the stats and chart."""
    solara.lab.theme.dark = True
    current = solara.use_reactive(model)
    view = solara.use_reactive(renderer)
    parameters = solara.use_reactive({})
    play_interval = solara.use_reactive(200)
    render_interval = solara.use_reactive(1)
    use_threads = solara.use_reactive(False)

    with solara.AppBar():
        solara.AppBarTitle(
            "Computational Systemics — Schelling Operational Status"
        )

    with solara.Sidebar():
        with solara.Column():
            with solara.Card("Controls"):
                solara.SliderInt(
                    label="Play Interval (ms)",
                    value=play_interval,
                    on_value=play_interval.set,
                    min=1,
                    max=500,
                    step=10,
                )
                solara.SliderInt(
                    label="Render Interval (steps)",
                    value=render_interval,
                    on_value=render_interval.set,
                    min=1,
                    max=100,
                    step=2,
                )
                solara.Checkbox(
                    label="Use Threads",
                    value=use_threads,
                    on_value=use_threads.set,
                )
                ModelController(
                    current,
                    renderer=view,
                    model_parameters=parameters,
                    play_interval=play_interval,
                    render_interval=render_interval,
                    use_threads=use_threads,
                )
            with solara.Card("Model Parameters"):
                ModelCreator(current, model_params, model_parameters=parameters)
            with solara.Card("Information"):
                ShowSteps(current.value)

    # 13:7 is about 65% grid, 35% stats and chart.
    with solara.Columns([13, 7], style={"padding": "12px", "align-items": "flex-start"}):
        SpaceRendererComponent(current.value, view.value)
        with solara.Column():
            status_panel(current.value)
            _plot_component(current.value)

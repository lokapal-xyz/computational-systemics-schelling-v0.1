"""Run one Schelling Operational Status simulation and print the step log."""

from __future__ import annotations

import argparse

from schelling_status import SchellingModel


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the v0.1 Schelling Operational Status model."
    )
    parser.add_argument("--width", type=int, default=50, help="Grid width (default 50).")
    parser.add_argument("--height", type=int, default=50, help="Grid height (default 50).")
    parser.add_argument(
        "--vacancy-rate",
        type=float,
        default=0.15,
        help="Fraction of empty cells (default 0.15).",
    )
    parser.add_argument(
        "--permeability",
        type=float,
        default=0.4,
        help="Tolerance threshold in [0, 1] (default 0.4).",
    )
    parser.add_argument(
        "--types",
        type=int,
        default=2,
        help="Number of fronterization values (default 2).",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=150,
        help="Maximum steps (default 150). Stops sooner if nobody is dissatisfied.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1,
        help="RNG seed (default 1).",
    )
    args = parser.parse_args()

    model = SchellingModel(
        grid_width=args.width,
        grid_height=args.height,
        vacancy_rate=args.vacancy_rate,
        permeability=args.permeability,
        n_types=args.types,
        steps=args.steps,
        seed=args.seed,
    )
    while model.running and model.steps < model.max_steps:
        model.step()

    frame = model.datacollector.get_model_vars_dataframe()
    frame.index.name = "step"
    print(
        frame.to_string(
            formatters={
                "dissatisfied": "{:.0f}".format,
                "moves": "{:.0f}".format,
                "segregation_index": "{:.4f}".format,
            }
        )
    )
    print()
    initial = frame.iloc[0]
    final = frame.iloc[-1]
    print(f"permeability:              {model.permeability:.2f}")
    print(f"initial segregation index: {initial['segregation_index']:.4f}")
    print(f"final segregation index:   {final['segregation_index']:.4f}")
    print(f"final dissatisfied:        {int(final['dissatisfied'])}")
    print(f"total moves:               {int(frame['moves'].sum())}")
    print(f"steps run:                 {len(frame) - 1}")
    if not model.running:
        print("stopped: no dissatisfied agents")
    else:
        print("stopped: reached max steps")


if __name__ == "__main__":
    main()

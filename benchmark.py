"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 21/03/2025
"""

import matplotlib.pyplot as plt

from typing import Any

from tqdm import tqdm
from run import model, reset_model
from utils import Color


def count_colors(state: dict[str, Any]) -> dict[Color, int]:
    count = {color: 0 for color in Color}
    for waste in state["wastes"]:
        count[waste["color"]] += 1
    for agent in state["agents"]:
        for waste_color in agent["inventory"]:
            count[waste_color] += 1
    return count


def update_curves(history: list[dict[str, Any]], curves: dict[Color, list[int]]) -> None:
    for i, h in enumerate(history):
        for color, count in count_colors(h).items():
            curves[color][i] += count


def play(curves: dict[Color, list[int]], steps: int) -> None:
    reset_model()
    model.value.run(steps)
    update_curves(model.value.history, curves)


def benchmark(t: int = 100) -> dict[Color, list[int]]:
    steps = 400
    curves = {color: [0] * steps for color in Color}

    for _ in tqdm(range(t)):
        play(curves, steps)

    return curves


if __name__ == "__main__":
    curves = benchmark()

    for color, values in curves.items():
        plt.plot(values, label=color.name, color=color.to_hex())

    plt.xlabel("Steps")
    plt.ylabel("Count")
    plt.title("Waste Count Over Time")
    plt.legend()
    plt.show()

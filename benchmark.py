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


def count_wastes(state: dict[str, Any]) -> int:
    count = len(state["wastes"])
    for agent in state["agents"]:
        count += len(agent["inventory"])
    return count


def update_curve(history: list[dict[str, Any]], curve: list[int]) -> None:
    for i, h in enumerate(history):
        curve[i] += count_wastes(h)


def play(agents_model: str, curve: list[int], steps: int) -> None:
    reset_model(**{f"{color.name.lower()}_agent_model": agents_model for color in Color})
    model.value.run(steps)
    update_curve(model.value.history, curve)


def benchmark(agents_model: str, n_run: int = 100, steps: int = 400) -> list[int]:
    curve = [0] * steps

    for _ in tqdm(range(n_run)):
        play(agents_model, curve, steps)

    return curve


if __name__ == "__main__":
    for agent_model in ["Random", "RuleBased", "DQN"]:
        curve = benchmark(agent_model)
        plt.plot(curve, label=f"{agent_model}")

    plt.xlabel("Steps")
    plt.ylabel("Count")
    plt.title("Waste Count Over Time")
    plt.legend()
    plt.show()

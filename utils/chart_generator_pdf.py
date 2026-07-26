import matplotlib.pyplot as plt
import os
import random
import textwrap


def generate_chart(chart_data, index):

    if not chart_data:
        return None

    labels = chart_data.get("labels", [])
    values = chart_data.get("values", [])

    chart_type = chart_data.get("type", "bar")
    title = chart_data.get("title", "Analysis")

    # ---------- VALIDATION ----------
    if not labels or not values:
        return None

    if len(labels) != len(values):
        min_len = min(len(labels), len(values))
        labels = labels[:min_len]
        values = values[:min_len]

    # ---------- RANDOMIZE INVALID TYPES ----------
    if chart_type not in ["bar", "line", "pie"]:
        chart_type = random.choice(["bar", "line", "pie"])

    os.makedirs("outputs", exist_ok=True)

    chart_path = f"outputs/chart_{index}.png"

    # ==================================================
    # LARGER FIGURE FOR PDF QUALITY
    # ==================================================

    plt.figure(figsize=(10, 6))

    # ==================================================
    # PLOT TYPES
    # ==================================================

    if chart_type == "line":

        plt.plot(
            labels,
            values,
            marker="o",
            linewidth=2.5,
            markersize=8
        )

    elif chart_type == "pie":

        plt.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90
        )

        plt.axis("equal")

    else:

        plt.bar(
            labels,
            values
        )

    # ==================================================
    # TITLE WRAPPING
    # ==================================================

    wrapped_title = "\n".join(
        textwrap.wrap(title, width=45)
    )

    plt.title(
        wrapped_title,
        fontsize=14,
        fontweight="bold",
        pad=20
    )

    # ==================================================
    # AXIS FORMATTING
    # ==================================================

    if chart_type != "pie":

        plt.xlabel(
            "Category",
            fontsize=12,
            labelpad=12
        )

        plt.ylabel(
            "Value",
            fontsize=12,
            labelpad=30
        )

        plt.xticks(
            rotation=15,
            fontsize=10
        )

        plt.yticks(
            fontsize=10
        )

        plt.grid(
            axis="y",
            linestyle="--",
            alpha=0.4
        )

    # ==================================================
    # SPACING
    # ==================================================

    plt.tight_layout(
        rect=[0.03, 0.03, 0.97, 0.93]
    )

    # ==================================================
    # HIGH QUALITY SAVE
    # ==================================================

    plt.savefig(
        chart_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    return chart_path

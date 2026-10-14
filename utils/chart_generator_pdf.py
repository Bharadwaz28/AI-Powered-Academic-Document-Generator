
import matplotlib.pyplot as plt
import os
import math
import textwrap


def generate_chart(chart_data, index):

    if not isinstance(chart_data, dict) or not chart_data:
        return None

    labels = chart_data.get("labels", [])
    values = chart_data.get("values", [])

    chart_type = chart_data.get("type", "bar")
    title = chart_data.get("title", "Analysis")

    # ---------- VALIDATION ----------

    if not isinstance(labels, list) or not isinstance(values, list):
        print(f"Chart {index}: labels and values must be lists.")
        return None

    if len(labels) < 2 or len(labels) != len(values):
        print(f"Chart {index}: invalid labels/values.")
        return None

    if chart_type not in ["bar", "line", "pie"]:
        print(f"Chart {index}: invalid chart type '{chart_type}'.")
        return None

    try:
        labels = [str(label).strip() for label in labels]
        values = [float(value) for value in values]
    except (TypeError, ValueError):
        print(f"Chart {index}: invalid chart values.")
        return None

    if (
        any(not label for label in labels)
        or any(not math.isfinite(value) for value in values)
    ):
        print(f"Chart {index}: empty labels or non-finite values.")
        return None

    if chart_type == "pie":
        if any(value < 0 for value in values) or sum(values) <= 0:
            print(f"Chart {index}: invalid pie-chart values.")
            return None

    # ---------- OUTPUT PATH ----------

    os.makedirs("outputs", exist_ok=True)
    chart_path = f"outputs/chart_{index}.png"

    fig, ax = plt.subplots(figsize=(10, 6))

    try:

        # ---------- PLOT TYPES ----------

        if chart_type == "line":
            ax.plot(
                labels,
                values,
                marker="o",
                linewidth=2.5,
                markersize=8
            )

        elif chart_type == "pie":
            ax.pie(
                values,
                labels=labels,
                autopct="%1.1f%%",
                startangle=90
            )
            ax.axis("equal")

        else:
            ax.bar(labels, values)

        # ---------- TITLE ----------

        wrapped_title = "\n".join(
            textwrap.wrap(str(title), width=45)
        )

        ax.set_title(
            wrapped_title,
            fontsize=14,
            fontweight="bold",
            pad=20
        )

        # ---------- AXIS FORMATTING ----------

        if chart_type != "pie":
            ax.set_xlabel(
                "Category",
                fontsize=12,
                labelpad=12
            )

            ax.set_ylabel(
                "Value",
                fontsize=12,
                labelpad=30
            )

            ax.tick_params(axis="x", labelrotation=15, labelsize=10)
            ax.tick_params(axis="y", labelsize=10)

            ax.grid(
                axis="y",
                linestyle="--",
                alpha=0.4
            )

        # ---------- SPACING ----------

        fig.tight_layout(rect=[0.03, 0.03, 0.97, 0.93])

        # ---------- HIGH-QUALITY OUTPUT ----------

        fig.savefig(
            chart_path,
            dpi=300,
            bbox_inches="tight"
        )

        if not os.path.isfile(chart_path) or os.path.getsize(chart_path) == 0:
            print(f"Chart {index}: PNG file was not created.")
            return None

        print(f"Chart {index} saved: {chart_path}")
        return chart_path

    except Exception as exc:
        print(f"Chart {index} rendering failed: {exc}")
        return None

    finally:
        plt.close(fig)

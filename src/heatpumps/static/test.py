import matplotlib.pyplot as plt


def generate_waterfall_diagram():
    fig, ax = plt.subplots()  # Create figure explicitly
    ax.bar(["A", "B", "C"], [10, -5, 15])  # Example waterfall data
    return fig  # Ensure the figure is returned

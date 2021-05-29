import pickle
import random
import matplotlib.pyplot as plt
from itertools import groupby
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List
import json

with open("config.json", "rb") as f:
    config = json.load(f)

excluded_drivers = config["race_visualization"]["excluded_drivers"]
sns.set_theme(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})
sector_dict = {}

distribution_offset = {
    1: config["race_visualization"]["distribution_offset"][0],
    2: config["race_visualization"]["distribution_offset"][1],
    3: config["race_visualization"]["distribution_offset"][2]
}

max_times = {
    1: config["race_visualization"]["max_times"][0],
    2: config["race_visualization"]["max_times"][1],
    3: config["race_visualization"]["max_times"][2]
}

min_times = {
    1: config["race_visualization"]["min_times"][0],
    2: config["race_visualization"]["min_times"][1],
    3: config["race_visualization"]["min_times"][2]
}

team_color = {k: v for d in config["teams"] for k, v in d.items()}


def create_sector_df(sector: int, group_laps=True, relative_times=False):
    global sector_dict
    if len(sector_dict) == 0:
        raise Exception("Please load the sector dict before creating a DataFrame")

    df = pd.DataFrame(index=np.arange(0, 1000))
    grouped_sectors = []
    global excluded_drivers
    for driver in drivers.keys():
        if driver not in excluded_drivers:
            if group_laps:
                grouped_sectors = [x[0] for x in groupby(sector_dict[driver][sector])]

            df[driver] = pd.Series(grouped_sectors if group_laps else sector_dict[driver][sector])
            df[driver] = df[driver].where(df[driver].between(min_times[sector], max_times[sector]))

            if relative_times:
                df[driver] = df[driver].apply(lambda x: x - df[driver].sum() / df[driver].count())

            df[f"{driver} (avg. {round(df[driver].sum() / df[driver].count(), 2)})"] = df[driver]
            df = df.drop([driver], axis=1)
    df = df.dropna(0, how="all").reset_index(drop=True)

    return df


def plot_driver_comparisons(to_compare: List[str]):
    if not all(x in drivers.keys() for x in to_compare):
        raise Exception("One or more of the drivers is not in the drivers list")

    if not len(to_compare) >= 2:
        raise Exception("Please provide at least 2 drivers to compare")

    def random_color():
        rand = lambda: random.randint(0, 200)
        return '#%02X%02X%02X' % (rand(), rand(), rand())

    def custom_color(color):
        color = color.lstrip('#')
        color = int(color, 16)
        comp_color = 0xFFFFFF ^ color
        comp_color = "#%06X" % comp_color
        comp_color = '#0' + comp_color[2:]
        return comp_color

    palette = [drivers[x] for x in to_compare]
    for i in range(len(palette)):
        if palette.count(palette[i]) > 1:
            palette[i] = custom_color(palette[i]) if len(palette) == 2 else random_color()

    for sector in [1, 2, 3]:
        df = create_sector_df(sector, group_laps=True)
        # Reindex df to represent the color palette (sort by to_compare index)
        df = df.reindex(sorted(df.columns, key=lambda c: to_compare.index(c[:3]) if c[:3] in to_compare else 100), axis=1)
        df = df[df.columns[:len(to_compare)]]
        for col in df.columns:
            df[col] = df[col].dropna(0).reset_index(drop=True)

        g = sns.relplot(data=df[[col for col in df.columns if any(x in col for x in to_compare)]],
                        kind="line", dashes=False, palette=palette)
        g.set(ylabel="Time (s)")
        plt.show()
        g.savefig(f"output/COMPARISON_S{sector}")


def plot_sector_distributions():
    for sector in [1, 2, 3]:
        df = create_sector_df(sector, group_laps=True)

        # Sort by average sector time
        df = df.reindex(sorted(df.columns, key=lambda c: df[c].sum() / df[c].count()), axis=1)

        # Reorganize data into new DataFrame
        times = []
        time_driver = []
        for col in df.columns:
            times.append(distribution_offset[sector])
            time_driver.append(col)
            for value in df[col].values:
                times.append(value)
                time_driver.append(col)

        df2 = pd.DataFrame()
        df2["times"] = pd.Series(times)
        df2["driver"] = pd.Series(time_driver)
        df2 = df2.dropna(0).reset_index(drop=True)
        print(df2["driver"].value_counts())

        # Initialize the FacetGrid object
        palette = [drivers[x[:3]] for x in df.columns]
        g = sns.FacetGrid(df2, row="driver", hue="driver", palette=palette, aspect=15, height=.5)

        # Draw the densities in a few steps
        g.map(sns.kdeplot, "times",
              bw_adjust=.3, clip_on=False,
              fill=True, alpha=1, linewidth=1.5)
        g.map(sns.kdeplot, "times", clip_on=False, color="w", lw=2, bw_adjust=.3)
        g.map(plt.axhline, y=0, lw=2, clip_on=False)

        # Define and use a simple function to label the plot in axes coordinates
        def label(x, color, label):
            ax = plt.gca()
            ax.text(0, .5, label, fontweight="bold", color=color,
                    ha="left", va="center", transform=ax.transAxes)

        g.map(label, "times")
        g.set_xlabels(f'Time (s)')

        # Set the subplots to overlap
        g.fig.subplots_adjust(hspace=-.25)

        g.fig.suptitle(f"Sector {sector}", weight="bold")

        # Remove axes details that don't play well with overlap
        g.set_titles("")
        g.set(yticks=[])
        g.despine(bottom=True, left=True)

        # Save and show the plot
        g.savefig(f"output/DISTRIBUTION_S{sector}")
        plt.show()


def visualize_data(to_compare: List[str] = None):
    try:
        with open("output/sector_data", 'rb') as file:
            global sector_dict
            sector_dict = pickle.load(file)

            global drivers
            drivers = {x["name"]: team_color[x["team"]] for x in config["drivers"]
                       if x["name"] in sector_dict and len(sector_dict[x["name"]]) > 2}

            if to_compare:
                plot_driver_comparisons(to_compare)

            plot_sector_distributions()

    except FileNotFoundError as e:
        print("You need to gather and process the screenshots before visualizing")
        raise e

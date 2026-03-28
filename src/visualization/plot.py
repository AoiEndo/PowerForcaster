"""Simple plotting helpers using matplotlib / seaborn."""
import matplotlib.pyplot as plt
import seaborn as sns

def plot_series(df, time_col, value_col, ax=None, title=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(10,4))
    sns.lineplot(data=df, x=time_col, y=value_col, ax=ax)
    if title:
        ax.set_title(title)
    return ax

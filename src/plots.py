import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd



# -------------------- Plots --------------------

def boxplot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    order: list | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    figsize: tuple = (12, 6),
    palette: str | list = "pastel",
    showfliers: bool = False,
    box_width: float = 0.5,
    add_points: bool = True,
    point_color: str = "black",
    point_alpha: float = 0.5,
    point_size: float = 4,
    point_jitter: bool = True,
    rotate_xticks: int | float = 0,
    grid_y: bool = True,
    ylim: tuple | None = None,
):
    """
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing the data.
        
    x_col : str
        Column name for categorical/groups (x-axis).
        
    y_col : str
        Column name for numeric values (y-axis).
        
    order : list, optional
        Explicit order of categories on x-axis. If None, inferred from data.
        
    title, xlabel, ylabel : str, optional
        Text labels. If None, reasonable defaults are used.
        
    figsize : tuple
        Figure size in inches.
        
    palette : str or list
        Seaborn palette name or list of colors. Sized automatically to groups.
        
    showfliers : bool
        Whether to show outliers in the boxplot.
        
    box_width : float
        Width of the box elements.
        
    add_points : bool
        If True, overlay jittered points (strip plot).
        
    point_color : str
        Color for the points.
        
    point_alpha : float
        Alpha for the points.
        
    point_size : float
        Marker size for the points.
        
    point_jitter : bool
        Whether to jitter points horizontally.
        
    rotate_xticks : int or float
        Degrees to rotate x-axis tick labels.
        
    grid_y : bool
        If True, add a faint horizontal grid.
        
    ylim : tuple, optional
        (ymin, ymax) limits for the y-axis.
    """
    sns.set(style="whitegrid", font_scale=1.1)

    # determine category order
    if order is None:
        # Preserve the order of appearance
        order = list(pd.Index(df[x_col]).astype("category").cat.categories) \
                if pd.api.types.is_categorical_dtype(df[x_col]) \
                else list(pd.unique(df[x_col]))

    # build a palette with number of colors
    if isinstance(palette, str):
        palette = sns.color_palette(palette, n_colors = len(order))
    else:
        if len(palette) < len(order):
            times = -(-len(order) // len(palette))  
            palette = (palette * times)[:len(order)]
        else:
            palette = palette[:len(order)]

    fig, ax = plt.subplots(figsize = figsize)

    # boxplot 
    sns.boxplot(
        data = df,
        x = x_col,
        y = y_col,
        hue = x_col,
        order = order,
        palette = palette,
        width = box_width,
        showfliers = showfliers,
        legend = False,
        ax = ax,
    )

    # optional points
    if add_points:
        sns.stripplot(
            data = df,
            x = x_col,
            y = y_col,
            order = order,
            color = point_color,
            alpha = point_alpha,
            jitter = point_jitter,
            size = point_size,
            ax = ax,
        )

    # labels & aesthetics
    ax.set_title(title if title is not None else "Boxplot", pad = 15)
    ax.set_xlabel(xlabel if xlabel is not None else x_col)
    ax.set_ylabel(ylabel if ylabel is not None else y_col)

    if rotate_xticks:
        ax.set_xticklabels(ax.get_xticklabels(), rotation = rotate_xticks, ha = "right")

    if grid_y:
        ax.grid(True, axis = "y", linestyle = "--", alpha = 0.2)

    if ylim is not None:
        ax.set_ylim(*ylim)

    fig.tight_layout()
    plt.show()
    
    return fig, ax

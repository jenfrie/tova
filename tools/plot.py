from datetime import datetime
from typing import Optional, Union, Tuple, List, Dict

import matplotlib
import matplotlib.pyplot as plt

TITLE_ON = False

matplotlib.rcParams.update({"font.size": 16,
                            "axes.prop_cycle": matplotlib.cycler(color=["#555c9d", "#ff8c78", "#842c61", "#e4cc27", "#51939a", "#316631"]),
                            "figure.figsize": (7.5, 3.0)})


def hist(x: list, y: Union[list, dict], title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, overlay: bool = False, perc: bool = False, annotations: Optional[List[tuple]] = None, xlim: Optional[Tuple[float, float]] = None, ylim: Optional[Tuple[float, float]] = None, yscale: Optional[str] = None, width: Optional[float] = None, horizontal: bool = False, style: Optional[Dict[str, Tuple[str, str]]] = None):
    x_is_str = isinstance(x[0], str)
    x_is_dt = isinstance(x[0], datetime)
    x_is_int = isinstance(x[0], int)
    y_is_dict = isinstance(y, dict)
    overlay = overlay or x_is_dt
    max_y = 0
    legend = False
    width = width if width else (0.8 if overlay else 0.8 / len(y))

    if (y_is_dict or isinstance(y[0], list)) and len(y) > 1:
        y_iter = y.items() if y_is_dict else ((None, y_val) for y_val in y)
        i = -(len(y) - 1)

        for label, y_val in y_iter:
            if isinstance(y_val, tuple):
                x_val, y_val = y_val
            if label:
                legend = True
            max_y = max(y_val) if max(y_val) > max_y else max_y
            y_val = [100 * val / sum(y_val) for val in y_val] if perc else y_val
            x_val = (x if x_is_int else [ind for ind, _ in enumerate(x)]) if overlay else ([ind + i * 0.5 * width for ind, _ in enumerate(x)] if x_is_str else [val + i * 0.5 * width for val in x])

            if style:
                hatch, color = style[label]
                if horizontal:
                    plt.barh(x_val, y_val, label=label, height=width, hatch=hatch, color=color, edgecolor="white", linewidth=2)
                else:
                    plt.bar(x=x_val, height=y_val, label=label, width=width, hatch=hatch, color=color, edgecolor="white", linewidth=2)
            else:
                if horizontal:
                    plt.barh(x_val, y_val, label=label, height=width)
                else:
                    plt.bar(x=x_val, height=y_val, label=label, width=width)

            i += 2
    else:
        y = list(y.values())[0] if y_is_dict else y
        max_y = max([v for v in y if v is not None])
        y = [100 * val / sum(y) for val in y] if perc else y
        if horizontal:
            plt.barh(x, y)
        else:
            plt.bar(x=x, height=y)

    if annotations:
        for co_x, co_y, text in annotations:
            plt.text(co_x, co_y, text, ha="center")

    if TITLE_ON:
        plt.title(title)
    plt.xlabel(xlabel if not horizontal else ylabel)
    plt.ylabel(ylabel if not horizontal else xlabel)
    if not horizontal:
        plt.ylim(ylim if ylim else ((0, 105) if perc else (0, 1.05 * max_y)))
    if yscale:
        plt.yscale(yscale)
    if xlim:
        plt.xlim(xlim)
    if x_is_str:
        if horizontal:
            plt.yticks(list(range(len(x))), x)
        else:
            plt.xticks(list(range(len(x))), x)
    if (x_is_dt or (x_is_str and any(len(s) > 3 for s in x))) and not horizontal:
        plt.xticks(rotation=35, ha="right")
    if legend:
        plt.legend()
    plt.grid(axis="y", color="gainsboro")
    plt.gca().set_axisbelow(True)
    plt.tight_layout()
    plt.savefig((title or "graph").lower().replace(" ", "_").replace("#", "n").replace("%", "prc") + ".pdf")
    plt.close()


def hist2x(x: list, y1: list, y2: list, title: Optional[str] = None, xlabel: Optional[str] = None, y1label: Optional[str] = None, y2label: Optional[str] = None, y1lim: Optional[Tuple[float, float]] = None, y2lim: Optional[Tuple[float, float]] = None):
    x_is_str = isinstance(x[0], str)
    x_is_dt = isinstance(x[0], datetime)
    max_y1 = max([v for v in y1 if v is not None])
    max_y2 = max([v for v in y2 if v is not None])
    legend = False
    width = 0.4

    fig, ax1 = plt.subplots()
    color1, color2 = plt.rcParams['axes.prop_cycle'].by_key()['color'][:2]

    x1 = [ind - 0.5 * width for ind, _ in enumerate(x)] if x_is_str else [val - 0.5 * width for val in x]
    ax1.bar(x=x1, height=y1, color=color1, width=width)

    x2 = [ind + 0.5 * width for ind, _ in enumerate(x)] if x_is_str else [val + 0.5 * width for val in x]
    ax2 = ax1.twinx()
    ax2.bar(x=x2, height=y2, color=color2, width=width)

    if TITLE_ON:
        plt.title(title)
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(y1label, color=color1)
    ax2.set_ylabel(y2label, color=color2)
    ax1.set_ylim(y1lim if y1lim else (0, 1.05 * max_y1))
    ax2.set_ylim(y2lim if y2lim else (0, 1.05 * max_y2))
    if x_is_str:
        plt.xticks(list(range(len(x))), x)
    if x_is_dt or (x_is_str and any(len(s) > 2 for s in x)):
        plt.xticks(rotation=35, ha="right")
    if legend:
        plt.legend()
    #plt.grid(axis="y", color="gainsboro")
    #plt.gca().set_axisbelow(True)
    plt.tight_layout()
    plt.savefig((title or "graph").lower().replace(" ", "_").replace("#", "n").replace("%", "prc") + ".pdf")
    plt.close()


def container_stats(x: list, y: Union[list, dict], title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, xlim: Optional[Tuple[float, float]] = None, ylim: Optional[Tuple[float, float]] = None, logscalex: bool = False, logscaley: bool = False):
    x_is_str = isinstance(x[0], str)
    x_is_dt = isinstance(x[0], datetime)
    x_is_num = isinstance(x[0], int) or isinstance(x[0], float)
    y_is_dict = isinstance(y, dict)
    max_y = []
    legend = False

    if (y_is_dict or isinstance(y[0], list)) and len(y) > 1:
        y_iter = y.items() if y_is_dict else ((None, y_val) for y_val in y)
        for label, y_val in y_iter:
            x_val = x
            if isinstance(y_val, tuple):
                x_val, y_val = y_val
            max_y.append(max(v for v in y_val if v is not None))
            if label and label.startswith("avg"):
                plt.plot(x_val, y_val, label=label, color="black")
                legend = True
            else:
                plt.plot(x_val, y_val, linestyle="--")
        max_y = max(max_y)

    else:
        y = list(y.values())[0] if y_is_dict else y
        max_y = max(v for v in y if v is not None)
        plt.plot(x, y)

    if TITLE_ON:
        plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if logscalex:
        plt.xscale("log")
    if logscaley:
        plt.yscale("log")
    plt.ylim(ylim if ylim else (0, 1.05 * max_y))
    if x_is_num:
        plt.xlim(xlim if xlim else (0, 1.05 * max(x)))

    if x_is_str:
        plt.xticks(list(range(len(x))), x)
    elif x_is_dt or (x_is_str and any(len(s) > 2 for s in x)):
        plt.xticks(rotation=35, ha="right")
    elif x_is_num:
        locs, labels = plt.xticks()
        plt.xticks([locs[i] for i in range(len(locs)) if "-" not in labels[i]._text and "." not in labels[i]._text], [time_format(int(label._text)) for label in labels if "-" not in label._text and "." not in label._text], rotation=35, ha="right")

    if legend:
        plt.legend()
    plt.grid(axis="y", color="gainsboro")
    plt.gca().set_axisbelow(True)
    plt.tight_layout()
    plt.savefig((title or "graph").lower().replace("/", "_").replace(" ", "_").replace("#", "n").replace("%", "prc") + ".pdf")
    plt.close()


def scatter(x: list, y: Union[list, dict], title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, size: float = 0.5, x_is_td: bool = False):
    x_is_num = isinstance(x[0], int) or isinstance(x[0], float)
    x_is_str = isinstance(x[0], str)
    x_is_dt = isinstance(x[0], datetime)
    y_is_dict = isinstance(y, dict)
    max_y, max_x = [], []
    legend = False

    if (y_is_dict or isinstance(y[0], list)) and len(y) > 1:
        y_iter = y.items() if y_is_dict else ((None, y_val) for y_val in y)
        for label, y_val in y_iter:
            x_val = x
            if isinstance(y_val, tuple):
                x_val, y_val = y_val
            if label:
                legend = True
            max_y.append(max(v for v in y_val if v is not None))
            max_x.append(max(v for v in x_val if v is not None))
            plt.scatter(x_val, y_val, label=label, s=size)
        max_y = max(max_y)
        max_x = max(max_x)

    else:
        max_y = max(v for v in y if v is not None)
        plt.scatter(x, y, s=size)

    if TITLE_ON:
        plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.ylim((0, 1.05 * max_y))
    if x_is_num:
        plt.xlim((0, 1.05 * max_x))
    if x_is_str:
        plt.xticks(list(range(len(x))), x)
    if x_is_dt or (x_is_str and any(len(s) > 2 for s in x)):
        plt.xticks(rotation=35, ha="right")
    elif x_is_td:
        locs, labels = plt.xticks()
        plt.xticks([locs[i] for i in range(len(locs)) if "-" not in labels[i]._text and "." not in labels[i]._text], [time_format(int(label._text)) for label in labels if "-" not in label._text and "." not in label._text], rotation=35, ha="right")
    if legend:
        plt.legend(scatterpoints=1, markerscale=5)
    plt.grid(axis="y", color="gainsboro")
    plt.gca().set_axisbelow(True)
    plt.tight_layout()
    plt.savefig((title or "graph").lower().replace(" ", "_").replace("#", "n").replace("%", "prc") + ".pdf")
    plt.close()


def boxplot(data: dict, title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, show_outliers: bool = True, horizontal: bool = False, logscale: bool = False):
    plt.figure(figsize=(6.5, 2.5))
    plt.boxplot(list(data.values()), labels=list(data.keys()), medianprops=dict(color="#ff8c78"), showfliers=show_outliers, vert=not horizontal)

    if TITLE_ON:
        plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if logscale:
        if horizontal:
            plt.xscale("log")
        else:
            plt.yscale("log")
    plt.grid(axis="y", color="gainsboro")
    plt.gca().set_axisbelow(True)
    plt.tight_layout()
    plt.savefig((title or "graph").lower().replace(" ", "_").replace("#", "n").replace("%", "prc") + ".pdf")
    plt.savefig((title or "graph").lower().replace(" ", "_").replace("#", "n").replace("%", "prc") + ".png")
    plt.close()


def line(x: list, y: Union[list, dict], title: Optional[str] = None, xlabel: Optional[str] = None, ylabel: Optional[str] = None, xlim: Optional[Tuple[float, float]] = None, ylim: Optional[Tuple[float, float]] = None, logscalex: bool = False, logscaley: bool = False, x_is_td: bool = False, side_legend: bool = False,  style: Optional[Dict[str, Tuple[str, str]]] = None):
    x_is_str = isinstance(x[0], str)
    x_is_dt = isinstance(x[0], datetime)
    x_is_num = isinstance(x[0], int) or isinstance(x[0], float)
    y_is_dict = isinstance(y, dict)
    max_y, max_x = [], []
    legend = False

    if (y_is_dict or isinstance(y[0], list)):
        y_iter = y.items() if y_is_dict else ((None, y_val) for y_val in y)
        for label, y_val in y_iter:
            x_val = x
            if isinstance(y_val, tuple):
                x_val, y_val = y_val
            if label:
                legend = True
            max_y.append(max(v for v in y_val if v is not None))
            max_x.append(max(v for v in x_val if v is not None))
            if style:
                linestyle, color = style[label]
                plt.plot(x_val, y_val, label=label, linestyle=linestyle, color=color)
            else:
                plt.plot(x_val, y_val, label=label)
        max_y = max(max_y)
        max_x = max(max_x)

    else:
        y = list(y.values())[0] if y_is_dict else y
        max_y = max(v for v in y if v is not None)
        max_x = max(v for v in x if v is not None)
        plt.plot(x, y)

    if TITLE_ON:
        plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if logscalex:
        plt.xscale("log")
    if logscaley:
        plt.yscale("log")
    plt.ylim(ylim if ylim else (0, 1.05 * max_y))
    if x_is_num:
        plt.xlim(xlim if xlim else (0, 1.05 * max_x))

    if x_is_str:
        plt.xticks(list(range(len(x))), x)
    elif x_is_dt or (x_is_str and any(len(s) > 2 for s in x)):
        plt.xticks(rotation=35, ha="right")
    elif x_is_td:
        locs, labels = plt.xticks()
        plt.xticks([locs[i] for i in range(len(locs)) if "−" not in labels[i]._text and "." not in labels[i]._text], [time_format(int(label._text)) for label in labels if "-" not in label._text and "." not in label._text], rotation=35, ha="right")

    if legend:
        if side_legend:
            plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        else:
            plt.legend()
    plt.grid(axis="y", color="gainsboro")
    plt.gca().set_axisbelow(True)
    plt.tight_layout()
    plt.savefig((title or "graph").lower().replace("/", "_").replace(" ", "_").replace("#", "n").replace("%", "prc") + ".pdf")
    plt.close()


def time_format(td: int) -> str:
    return "%02i:%02i:%02i" % (td // 3600, (td % 3600) / 60, td % 60)

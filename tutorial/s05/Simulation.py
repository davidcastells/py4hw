import wavedrom
import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.pyplot as plt


def drawDelayDiagram():
    # Define the WaveDrom signal structure
    dff_diagram = {"signal": [{"name": "clk", "wave": "0P....."},
            {"name": "D",   "wave": "01..0.1", "phase":-0.8},
            {"name": "Q",   "wave": "0.1..0.", "phase":-0.2}
        ],
        "head": {        "text": "D Flip-Flop Timing Diagram",        "tick": 0, "every":2    },
        "config": {        "hscale": 1.5    }
    }
    
    # Render the diagram inside the Jupyter Notebook
    return wavedrom.render(str(dff_diagram))



fs = 10

def draw_curly_brace(ax, x1, x2, y, text="", depth=0.12, color="blue", fontsize=11):
    """Draws a smooth vector curly brace pointing downward from x1 to x2 at level y."""
    xm = (x1 + x2) / 2.0
    r = min((x2 - x1) * 0.08, depth)  # Curve radius

    # Cubic Bézier control points for a clean brace
    verts = [
        (x1, y),  # Start
        (x1 , y - r),
        (x1 + r, y - depth / 2),
        (x1 + 2 * r, y - depth / 2),  # Left shoulder
        (xm - r, y - depth / 2),
        (xm - r, y - depth),
        (xm, y - depth),  # Left tip center
        (xm + r, y - depth),
        (xm + r, y - depth / 2),
        (x2 - 2 * r, y - depth / 2),  # Right tip center
        (x2 - r, y - depth / 2),
        (x2 , y -r),
        (x2, y),  # Right shoulder
    ]

    codes = [mpath.Path.MOVETO] + [mpath.Path.CURVE4] * 12
    path = mpath.Path(verts, codes)
    patch = mpatches.PathPatch(path, facecolor="none", edgecolor=color, lw=1.8, clip_on=False,zorder=10,)
    ax.add_patch(patch)

    if text:
        ax.text(xm, y - depth - 0.05, text, color=color, fontsize=fontsize, ha="center",va="top")

def drawSimulationRelatedFunctions():

    # 1. Define digital clock signal coordinates
    x_clk = [0, 4, 4, 8, 8, 11]
    y_clk = [0.5, 0.5, 1, 1, 0.5, 0.5]
    
    fig, ax = plt.subplots(figsize=(8, 2))
    
    # Plot clock line
    ax.plot(x_clk, y_clk, color="black", lw=1.5)
    
    # 2. Draw Black Rising-Edge Arrow
    ax.annotate(    "",    xy=(4, 1),    xytext=(4, 0.7),    arrowprops=dict(arrowstyle="->", color="black", lw=1.5, mutation_scale=20),)
    
    # 3. Annotate Downward Red Arrows and Labels
    annotations = [
        (1.2, 0.8, -0.25, "propagate", 1.2, -0.32),
        (3.0, 0.8, -0.25, "monitor", 3.0, -0.32),
        (4.0, 0.8, -0.25, "clock", 4.2, -0.32),
        (6.0, 0.8, -0.25, "propagate", 6.0, -0.32),
    ]
    
    for ax_x, ay_start, ay_end, text, tx, ty in annotations:
        ax.annotate(
            "",
            xy=(ax_x, ay_end),
            xytext=(ax_x, ay_start),
            arrowprops=dict(arrowstyle="->", color="red", lw=1.8, connectionstyle="arc3,rad=-0.15", mutation_scale=15,),
        )
        # fontweight="bold"
        ax.text(tx, ty, text, color="red", fontsize=fs, ha="center", va="top")
    
    # 4. Draw Pure-Python Curly Brace spanning x = 2.5 to 8.0
    draw_curly_brace(ax, x1=2.5, x2=10.0, y=-0.65, text="simulation cycle", depth=0.12, color="blue", fontsize=fs)
    
    # 5. Axis formatting
    ax.set_ylim(-1.2, 1.2)
    ax.set_xlim(-0.5, 14)
    ax.axis("off")
    
    plt.tight_layout()
    plt.show()
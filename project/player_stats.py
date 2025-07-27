import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from collections import defaultdict, Counter
from matplotlib.table import Table
import matplotlib.colors as mcolors
import matplotlib.cm as cm
from pandas.plotting import table as pd_table

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from scipy.stats import gaussian_kde
import numpy as np


def convert_min_to_float(min_str):
    minutes, seconds = map(int, min_str.split(":"))
    return minutes + seconds / 60


def scout_team(team_name: str, offensive_csv_path: str, defensive_csv_path: str, players_csv_path: str):
    base_dir = os.path.dirname(__file__)
    off_path = os.path.join(base_dir, offensive_csv_path)
    def_path = os.path.join(base_dir, defensive_csv_path)
    players_path = os.path.join(base_dir, players_csv_path)
    plots_dir = os.path.join(base_dir, "files", "plots")
    os.makedirs(plots_dir, exist_ok=True)

    df_off = pd.read_csv(off_path)
    df_def = pd.read_csv(def_path)
    df_players = pd.read_csv(players_path)

    df = pd.merge(df_off, df_def, on="team_name", suffixes=("", "r"))
    df["Min_float"] = df["Min"].apply(convert_min_to_float)

    # (Aquí irían todos los cálculos y llamadas a tus funciones gráficas anteriores...)

    # Crear tabla resumen jugadores del equipo
    df_team_players = df_players[df_players["team_name"] == team_name]
    player_table_path = create_player_summary_table(df_team_players, team_name, plots_dir)
    plot_path = cluster_and_plot_players_with_kde(df_players, selected_team=team_name, n_clusters=4, out_dir="files/plots")


    # Retornar paths junto con los demás gráficos (a añadir según tu código)
    return {
        # ... otros paths de gráficos ...
        "player_summary_table": player_table_path,
        "clustering": plot_path
    }


def cluster_and_plot_players_with_kde(df_all_players, selected_team, n_clusters=4, random_state=42, out_dir="."):

    df = df_all_players.copy()
    df["Min"] = df["Min"].apply(lambda x: sum(int(t) * 60 ** i for i, t in enumerate(reversed(x.split(":")))) / 60)
    per_game_stats = [
        "PTS", "2PM", "2PA", "3PM", "3PA", "FTM", "FTA",
        "OR", "DR", "TR", "AST", "STL", "TO", "BLK", "BLKA",
        "FC", "FD", "PIR", "Min"
    ]
    for stat in per_game_stats:
        df[stat] = df[stat] / df["GP"]
    features = per_game_stats + ["GP"]
    X = df[features].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
    clusters = kmeans.fit_predict(X_scaled)
    df["cluster"] = clusters
    pca = PCA(n_components=2, random_state=random_state)
    X_pca = pca.fit_transform(X_scaled)
    df["pca1"] = X_pca[:, 0]
    df["pca2"] = X_pca[:, 1]

    plt.figure(figsize=(14, 10))
    colors = plt.cm.tab10.colors

    for cluster_id in range(n_clusters):
        cluster_points = df[df["cluster"] == cluster_id]
        plt.scatter(cluster_points["pca1"], cluster_points["pca2"],
                    color=colors[cluster_id], alpha=0.4, label=f"Cluster {cluster_id}")
        # KDE contour
        xy = np.vstack([cluster_points["pca1"], cluster_points["pca2"]])
        kde = gaussian_kde(xy)
        xmin, xmax = cluster_points["pca1"].min() - 1, cluster_points["pca1"].max() + 1
        ymin, ymax = cluster_points["pca2"].min() - 1, cluster_points["pca2"].max() + 1
        xx, yy = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]
        positions = np.vstack([xx.ravel(), yy.ravel()])
        f = np.reshape(kde(positions).T, xx.shape)
        plt.contour(xx, yy, f, levels=3, colors=[colors[cluster_id]], alpha=0.7)

    team_players = df[df["team_name"] == selected_team]
    plt.scatter(team_players["pca1"], team_players["pca2"], color="black", s=80, label=f"{selected_team} players")

    for _, row in team_players.iterrows():
        plt.text(row["pca1"] + 0.02, row["pca2"], row["Player"], fontsize=9, weight='bold')

    plt.title(f"Player Clustering with KDE Contours — Highlight: {selected_team}", fontsize=18, weight="bold")
    plt.xlabel("PCA Dimension 1")
    plt.ylabel("PCA Dimension 2")
    plt.legend(loc="best")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{selected_team}_player_clusters_kde.png")
    plt.savefig(path, dpi=300)
    plt.close()
    return path

def render_player_summary_table(df, team_name, out_dir):
    display_cols = df.columns.tolist()
    
    # Normalizar cada columna numérica para color
    norm_df = df[display_cols].apply(lambda x: (x - x.min()) / (x.max() - x.min()) if x.dtype != "O" else x)
    cmap = plt.cm.Greens

    # Crear figura grande
    fig, ax = plt.subplots(figsize=(len(display_cols) * 1.5, len(df) * 0.7 + 2))
    ax.axis('off')

    # Crear tabla pandas con estilo
    tbl = pd_table(ax, df, loc='center', cellLoc='center', colWidths=[0.1]*len(df.columns))
    
    # Estilo visual
    for (i, j), cell in tbl.get_celld().items():
        if i == 0:
            cell.set_fontsize(18)
            cell.set_text_props(weight='bold')
            cell.set_facecolor("lightgrey")
        else:
            cell.set_fontsize(16)
            if df.columns[j] in norm_df.columns:
                val = norm_df.iloc[i-1, j]
                cell.set_facecolor(cmap(val))
    
    plt.title(f"{team_name} — Player Summary (Per Game Stats & Efficiency)", fontsize=24, weight="bold", pad=30)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{team_name}_players_summary_table.png")
    plt.savefig(path, dpi=400, bbox_inches='tight')
    plt.close()
    return path

def create_player_summary_table(df, team_name, out_dir):
    per_game_stats = [
        "PTS", "2PM", "2PA", "3PM", "3PA", "FTM", "FTA", "AST", "STL", "TO", "BLK", "BLKA", "FC", "FD", "PIR"
    ]

    df = df[df["team_name"] == team_name].copy()
    df["Min"] = df["Min"].apply(lambda x: sum(int(t) * 60 ** i for i, t in enumerate(reversed(x.split(":")))) / 60)
    df["Min"] = df["Min"] / df["GP"]

    for stat in per_game_stats:
        df[stat] = df[stat] / df["GP"]

    df["Poss"] = df["2PA"] + df["3PA"] + 0.44 * df["FTA"] + df["TO"]
    df["OER"] = df["PTS"] / (df["Poss"] + 1e-6)

    df["FGA"] = df["2PA"] + df["3PA"]
    df["FTA_rate"] = df["FTA"] / (df["FGA"] + 1e-6)
    df["ORB%"] = df["OR"] / (df["OR"] + df["DR"] + 1e-6)
    df["TOV%"] = df["TO"] / (df["Poss"] + 1e-6)
    df["eFG%"] = (df["2PM"] + 0.5 * df["3PM"]) / (df["2PA"] + df["3PA"] + 1e-6)

    df = df.fillna(0)
    df = df.sort_values("OER", ascending=False)

    display_stats = [
        "Player", "GP", "Min", "PTS", "2PM", "2PA", "3PM", "3PA", "FTM", "FTA", "AST", "STL", "TO", "FC", "FD", "PIR"
    ]
    display_eff = [
        "Player", "Poss", "OER", "eFG%", "FTA_rate", "ORB%", "TOV%"
    ]

    df_stats = df[display_stats].copy()
    df_stats["Min"] = df_stats["Min"].round(1)
    df_stats = df_stats.round(2)
    df_stats.reset_index(drop=True, inplace=True)

    df_eff = df[display_eff].copy()
    df_eff = df_eff.round(3)
    df_eff.reset_index(drop=True, inplace=True)

    norm_stats = df_stats.copy()
    norm_eff = df_eff.copy()

    for col in df_stats.columns:
        if col != "Player":
            col_min, col_max = df_stats[col].min(), df_stats[col].max()
            norm_stats[col] = (df_stats[col] - col_min) / (col_max - col_min + 1e-6)

    for col in df_eff.columns:
        if col != "Player":
            col_min, col_max = df_eff[col].min(), df_eff[col].max()
            norm_eff[col] = (df_eff[col] - col_min) / (col_max - col_min + 1e-6)

    cmap = cm.Greens
    col_widths_stats = [0.25] + [0.04] * (len(display_stats) - 1)
    col_widths_eff = [0.25] + [0.06] * (len(display_eff) - 1)

    fig, axs = plt.subplots(2, 1, figsize=(sum(col_widths_stats) * 10, len(df_stats) * 1.0 + 3.5))

    # Reducir el espacio vertical entre tablas y acercar título a la primera tabla
    fig.subplots_adjust(hspace=0.01, top=0.43)

    for ax in axs:
        ax.axis('off')

    def hide_index_cells(tbl):
        for (i, j), cell in tbl.get_celld().items():
            if j == -1:  # índice
                cell.set_visible(False)

    tbl_stats = pd_table(axs[0], df_stats, loc='center', cellLoc='center', colWidths=col_widths_stats)
    hide_index_cells(tbl_stats)
    for (i, j), cell in tbl_stats.get_celld().items():
        if i == 0:
            cell.set_fontsize(36)
            cell.set_text_props(weight='bold')
            cell.set_facecolor("lightgrey")
        else:
            cell.set_fontsize(34)
            if df_stats.columns[j] != "Player":
                cell.set_facecolor(cmap(norm_stats.iloc[i-1, j]))

    tbl_eff = pd_table(axs[1], df_eff, loc='center', cellLoc='center', colWidths=col_widths_eff)
    hide_index_cells(tbl_eff)
    for (i, j), cell in tbl_eff.get_celld().items():
        if i == 0:
            cell.set_fontsize(36)
            cell.set_text_props(weight='bold')
            cell.set_facecolor("lightgrey")
        else:
            cell.set_fontsize(34)
            if df_eff.columns[j] != "Player":
                cell.set_facecolor(cmap(norm_eff.iloc[i-1, j]))

    #plt.suptitle(f"{team_name}", fontsize=20, weight="bold", y=0.97)

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{team_name}_players_summary_table.png")
    plt.savefig(path, dpi=800, bbox_inches='tight')
    plt.close()
    return path
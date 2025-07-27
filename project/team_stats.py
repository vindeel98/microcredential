import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from collections import defaultdict, Counter
from matplotlib.table import Table


def convert_min_to_float(min_str):
    minutes, seconds = map(int, min_str.split(":"))
    return minutes + seconds / 60

def scout_team(team_name: str, offensive_csv_path: str, defensive_csv_path: str):
    base_dir = os.path.dirname(__file__)
    off_path = os.path.join(base_dir, offensive_csv_path)
    def_path = os.path.join(base_dir, defensive_csv_path)
    plots_dir = os.path.join(base_dir, "files", "plots")
    os.makedirs(plots_dir, exist_ok=True)

    df_off = pd.read_csv(off_path)
    df_def = pd.read_csv(def_path)
    df = pd.merge(df_off, df_def, on="team_name", suffixes=("", "r"))

    df["Min_float"] = df["Min"].apply(convert_min_to_float)

    df["FGA"] = df["2PA"] + df["3PA"]
    df["FGM"] = df["2PM"] + df["3PM"]
    df["Poss"] = df["FGA"] + 0.44 * df["FTA"] + df["TO"] - df["OR"]
    df["FTA_rate"] = df["FTA"] / df["FGA"]
    df["ORB%"] = df["OR"] / (df["OR"] + df["DRr"])
    df["TOV%"] = df["TO"] / df["Poss"]
    df["eFG%"] = (df["FGM"] + 0.5 * df["3PM"]) / df["FGA"]
    df["FT%"] = df["FTM"] / df["FTA"]
    df["Pace"] = df["Poss"] / df["GP"]

    df["OER"] = df["PTS"] / df["Poss"]
    df["DER"] = df["PTSr"] / df["Poss"]
    df["Net"] = df["OER"] - df["DER"]

    df_sorted = df.sort_values(by="Net", ascending=False).reset_index(drop=True)
    table_path = render_table_as_image(df_sorted, team_name, plots_dir)

    scatter_path = create_oer_der_plot(df_sorted, team_name, plots_dir)
    bar_path = create_possessions_bar_chart(df, plots_dir, team_name)
    usage_paths = create_offensive_usage_charts(df, team_name, plots_dir)
    usage_paths["def_pie"] = create_defensive_usage_charts(df, team_name, plots_dir)
    ff_off_path = create_offensive_four_factors_chart(df, team_name, plots_dir)
    ff_def_path = create_defensive_four_factors_chart(df, team_name, plots_dir)


    return {
        "table": table_path,
        "scatter": scatter_path,
        "possessions": bar_path,
        "usage": usage_paths,
        "four_factors": {
            "off": ff_off_path,
            "def": ff_def_path,
        },
    }

def render_table_as_image(df, team_name, out_dir):
    cols = ["team_name", "Net", "OER", "DER"]
    df_table = df[cols].copy()

    # Normalizaciones para escalas de color
    norm_oer = plt.Normalize(df_table["OER"].min(), df_table["OER"].max())
    norm_der = plt.Normalize(df_table["DER"].min(), df_table["DER"].max())
    green_cmap = plt.cm.Greens
    red_cmap = plt.cm.Reds_r  # Rojo más intenso = peor defensa

    fig, ax = plt.subplots(figsize=(10, len(df_table) * 0.45 + 1))
    ax.axis('off')
    table = Table(ax, bbox=[0, 0, 1, 1])

    cell_height = 1 / (len(df_table) + 1)
    cell_width = 1 / len(cols)

    # Encabezados
    for i, col in enumerate(cols):
        table.add_cell(0, i, width=cell_width, height=cell_height, text=col, loc='center',
                       facecolor='lightgrey', fontproperties={'weight': 'bold', 'size': 10})

    # Filas de datos
    for row_idx, row in enumerate(df_table.itertuples(index=False), start=1):
        for col_idx, val in enumerate(row):
            col_name = cols[col_idx]
            # Color de fondo según condiciones
            if col_name == "team_name":
                facecolor = 'yellow' if val == team_name else 'white'
            elif col_name == "OER":
                facecolor = green_cmap(norm_oer(val))
            elif col_name == "DER":
                facecolor = red_cmap(norm_der(val))
            else:
                facecolor = 'white'

            text_val = f"{val:.2f}" if isinstance(val, float) else val
            table.add_cell(row_idx, col_idx, width=cell_width, height=cell_height,
                           text=text_val, loc='center', facecolor=facecolor,
                           fontproperties={'weight': 'bold', 'size': 10})

    ax.add_table(table)
    path = os.path.join(out_dir, f"{team_name}_efficiency_table.png")
    plt.savefig(path, bbox_inches='tight', dpi=150)
    plt.close()
    return path

def create_oer_der_plot(df, team_name, out_dir):

    plt.figure(figsize=(10, 6))

    # Crear columna temporal para saber si es el equipo que queremos
    df["_highlight"] = df["team_name"] == team_name

    # Dibujar puntos
    sns.scatterplot(
        data=df,
        x="OER",
        y="DER",
        hue="_highlight",
        palette={True: "red", False: "blue"},
        s=100,
        legend=False  
    )

    # Añadir etiquetas de texto
    for _, row in df.iterrows():
        plt.text(row["OER"] + 0.01, row["DER"], row["team_name"], fontsize=8)

    plt.xlabel("Offensive Efficiency (OER)")
    plt.ylabel("Defensive Efficiency (DER)")
    plt.title("OER vs DER (Team Comparison)")
    plt.grid(True)
    plt.tight_layout()

    path = os.path.join(out_dir, f"{team_name}_oer_der_comparison_plot.png")
    plt.savefig(path)
    plt.close()

    # Eliminar columna temporal
    df.drop(columns=["_highlight"], inplace=True)

    return path

def create_possessions_bar_chart(df, out_dir, team_name=None):

    df_sorted = df.sort_values("Pace", ascending=False).reset_index(drop=True)

    # Crear lista de colores: mismo color para todos excepto el equipo objetivo
    colors = ["#cccccc"] * len(df_sorted)
    if team_name in df_sorted["team_name"].values:
        team_index = df_sorted[df_sorted["team_name"] == team_name].index[0]
        colors[team_index] = "#1f77b4"  # azul para el equipo objetivo

    plt.figure(figsize=(12, 6))
    bars = sns.barplot(x="team_name", y="Pace", data=df_sorted, palette=colors)

    # Mostrar valor de posesiones encima de cada barra
    for i, row in df_sorted.iterrows():
        bars.text(i, row["Pace"] + 0.5, f"{row['Pace']:.1f}", ha="center", fontsize=9)

    plt.ylim(70, df_sorted["Pace"].max() + 5)
    plt.xticks(rotation=90)
    plt.ylabel("Possessions per game")
    plt.xlabel("Team")
    plt.title("Possessions per Game")
    plt.tight_layout()

    path = os.path.join(out_dir, f"{team_name}_posessions_per_game.png")
    plt.savefig(path)
    plt.close()
    return path

def create_offensive_usage_charts(df, team_name, out_dir):
    # Cálculos
    df["Uso2P"] = df["2PA"] / (df["2PA"] + df["3PA"] + df["FTA"])
    df["Uso3P"] = df["3PA"] / (df["2PA"] + df["3PA"] + df["FTA"])
    df["UsoFT"] = df["FTA"] / (df["2PA"] + df["3PA"] + df["FTA"])

    mean_uso = df[["Uso2P", "Uso3P", "UsoFT"]].mean()
    team_row = df[df["team_name"] == team_name][["Uso2P", "Uso3P", "UsoFT"]].iloc[0]
    diff_percent = ((team_row - mean_uso) / mean_uso) * 100
    labels = ["Usg% 2-Points", "Usg% 3-Points", "Usg% Free Throws"]

    # Pie chart
    plt.figure(figsize=(6, 6))
    plt.pie(team_row, labels=labels, autopct="%1.1f%%", startangle=140)
    plt.title(f"Offensive Shot Usage: {team_name}")
    usage_pie_path = os.path.join(out_dir, f"{team_name}_offensive_usage.png")
    plt.savefig(usage_pie_path)
    plt.close()

    # Bar chart
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, diff_percent, color="skyblue")
    plt.axhline(0, color="gray", linestyle="--")
    plt.title(f"Offensive Usage Difference vs League Average: {team_name}")
    plt.ylabel("Difference (%)")

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.5, f"{yval:.1f}%", ha='center', fontsize=10, fontweight='bold')

    # Leyenda comparativa fuera del gráfico
    lines = [
        f"{label}: Team {team_row[i]*100:.1f}%, League {mean_uso[i]*100:.1f}%"
        for i, label in enumerate(labels)
    ]
    legend_text = "\n".join(lines)
    plt.gcf().text(0.02, -0.05, legend_text, fontsize=9, va='top', bbox=dict(facecolor='white', edgecolor='black'))

    plt.tight_layout()
    usage_diff_path = os.path.join(out_dir, f"{team_name}_offensive_usage_diff.png")
    plt.savefig(usage_diff_path, bbox_inches='tight')
    plt.close()

    return {"pie": usage_pie_path, "diff": usage_diff_path}

def create_defensive_usage_charts(df, team_name, out_dir):
    # Cálculos defensivos (uso que los rivales hacen)
    df["Uso2Pr"] = df["2PAr"] / (df["2PAr"] + df["3PAr"] + df["FTAr"])
    df["Uso3Pr"] = df["3PAr"] / (df["2PAr"] + df["3PAr"] + df["FTAr"])
    df["UsoFTr"] = df["FTAr"] / (df["2PAr"] + df["3PAr"] + df["FTAr"])

    mean_uso = df[["Uso2Pr", "Uso3Pr", "UsoFTr"]].mean()
    team_row = df[df["team_name"] == team_name][["Uso2Pr", "Uso3Pr", "UsoFTr"]].iloc[0]
    diff_percent = ((team_row - mean_uso) / mean_uso) * 100
    labels = ["Usg% 2-Points", "Usg% 3-Points", "Usg% Free Throws"]

    # Pie chart
    plt.figure(figsize=(6, 6))
    plt.pie(team_row, labels=labels, autopct="%1.1f%%", startangle=140)
    plt.title(f"Defensive Shot Usage: {team_name}")
    usage_pie_path = os.path.join(out_dir, f"{team_name}_defensive_usage.png")
    plt.savefig(usage_pie_path)
    plt.close()

    # Bar chart (diferencia relativa)
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, diff_percent, color="indianred")
    plt.axhline(0, color="gray", linestyle="--")
    plt.title(f"Defensive Usage Difference vs League Average: {team_name}")
    plt.ylabel("Difference (%)")

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.5, f"{yval:.1f}%", ha='center', fontsize=10, fontweight='bold')

    # Leyenda comparativa
    lines = [
        f"{label}: Team {team_row[i]*100:.1f}%, League {mean_uso[i]*100:.1f}%"
        for i, label in enumerate(labels)
    ]
    legend_text = "\n".join(lines)
    plt.gcf().text(0.02, -0.05, legend_text, fontsize=9, va='top', bbox=dict(facecolor='white', edgecolor='black'))

    plt.tight_layout()
    usage_diff_path = os.path.join(out_dir, f"{team_name}_defensive_usage_diff.png")
    plt.savefig(usage_diff_path, bbox_inches='tight')
    plt.close()

    return {"pie": usage_pie_path, "diff": usage_diff_path}

def create_offensive_four_factors_chart(df, team_name, out_dir):
    ff_keys = ["eFG%", "FTA_rate", "ORB%", "TOV%"]
    team_ff = df[df["team_name"] == team_name][ff_keys].iloc[0]
    league_ff = df[ff_keys].mean()

    diff_percent = ((team_ff - league_ff) / league_ff) * 100

    labels = ["eFG%", "FTA Rate", "ORB%", "TOV%"]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, diff_percent, color="skyblue")
    plt.axhline(0, color="gray", linestyle="--")
    plt.title(f"Offensive Four Factors Difference vs League: {team_name}")
    plt.ylabel("Difference (%)")

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.5, f"{yval:.1f}%", ha='center', fontsize=10, fontweight='bold')

    # Leyenda comparativa debajo
    lines = [
        f"{label}: Team {team_ff[i]*100:.1f}%, League {league_ff[i]*100:.1f}%"
        for i, label in enumerate(labels)
    ]
    legend_text = "\n".join(lines)
    plt.gcf().text(0.02, -0.05, legend_text, fontsize=9, va='top', bbox=dict(facecolor='white', edgecolor='black'))

    plt.tight_layout()
    path = os.path.join(out_dir, f"{team_name}_four_factors_off.png")
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path


def create_defensive_four_factors_chart(df, team_name, out_dir):
    # Añadir columnas defensivas si no existen
    df["eFG%r"] = (df["2PMr"] + df["3PMr"] + 0.5 * df["3PMr"]) / (df["2PAr"] + df["3PAr"])
    df["FTA_r_rate"] = df["FTAr"] / (df["2PAr"] + df["3PAr"])
    df["ORB%r"] = df["ORr"] / (df["ORr"] + df["DR"])
    df["TOV%r"] = df["TOr"] / df["Poss"]

    ff_keys_r = ["eFG%r", "FTA_r_rate", "ORB%r", "TOV%r"]
    labels = ["eFG%", "FTA Rate", "ORB%", "TOV%"]

    team_ff_def = df[df["team_name"] == team_name][ff_keys_r].iloc[0]
    league_ff_def = df[ff_keys_r].mean()
    diff_percent = ((team_ff_def - league_ff_def) / league_ff_def) * 100

    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, diff_percent, color="indianred")
    plt.axhline(0, color="gray", linestyle="--")
    plt.title(f"Defensive Four Factors Difference vs League: {team_name}")
    plt.ylabel("Difference (%)")

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.5, f"{yval:.1f}%", ha='center', fontsize=10, fontweight='bold')

    # Leyenda comparativa debajo
    lines = [
        f"{label}: Team {team_ff_def[i]*100:.1f}%, League {league_ff_def[i]*100:.1f}%"
        for i, label in enumerate(labels)
    ]
    legend_text = "\n".join(lines)
    plt.gcf().text(0.02, -0.05, legend_text, fontsize=9, va='top', bbox=dict(facecolor='white', edgecolor='black'))

    plt.tight_layout()
    path = os.path.join(out_dir, f"{team_name}_four_factors_def.png")
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path


def get_team_defensive_stats_from_play_by_plays(play_by_play_folder: str, team_list_csv: str):
    base_dir = os.path.dirname(__file__)
    play_by_play_path = os.path.join(base_dir, play_by_play_folder)
    team_csv_path = os.path.join(base_dir, team_list_csv)

    # Leemos el CSV ofensivo para mantener el orden y nombres
    df_teams = pd.read_csv(team_csv_path)
    team_names = df_teams["team_name"].tolist()

    # Este es el orden y columnas que queremos replicar con sufijo "r"
    stat_fields = ['PTS','2PM','2PA','3PM','3PA','FTM','FTA','OR','DR','TR','AST','STL','TO','BLK','BLKA','FC','FD','PIR']

    team_stats = defaultdict(Counter)

    for filename in os.listdir(play_by_play_path):
        if not filename.endswith(".csv"):
            continue

        # Parsear nombre de equipos del archivo
        try:
            team1_raw = filename.split("game_")[1].split("_vs_")[0].replace("_", " ")
            team2_raw = filename.split("_vs_")[1].replace(".csv", "").replace("_", " ")
        except IndexError:
            continue

        teams_in_game = [team1_raw, team2_raw]
        file_path = os.path.join(play_by_play_path, filename)
        df = pd.read_csv(file_path)

        for team in teams_in_game:
            if team not in team_names:
                continue

            # Acciones que hace el rival contra este equipo
            for _, row in df.iterrows():
                if row["side"] == team:
                    continue  # Solo acciones del rival (contra este equipo)

                action = row["action_code"]
                stats = team_stats[team]

                if action == "2PM":
                    stats["2PM"] += 1
                    stats["PTS"] += 2
                    stats["2PA"] += 1
                elif action == "2PA":
                    stats["2PA"] += 1
                elif action == "3PM":
                    stats["3PM"] += 1
                    stats["PTS"] += 3
                    stats["3PA"] += 1
                elif action == "3PA":
                    stats["3PA"] += 1
                elif action == "FTM":
                    stats["FTM"] += 1
                    stats["PTS"] += 1
                    stats["FTA"] += 1
                elif action == "FTA":
                    stats["FTA"] += 1
                elif action == "OREB":
                    stats["OR"] += 1
                elif action == "DREB":
                    stats["DR"] += 1
                elif action == "TOV":
                    stats["TO"] += 1
                elif action == "AST":
                    stats["AST"] += 1
                elif action == "STL":
                    stats["STL"] += 1
                elif action == "BLK":
                    stats["BLK"] += 1
                elif action == "BLKRec":
                    stats["BLKA"] += 1
                elif action == "PF":
                    stats["FC"] += 1
                elif action in ("PFRec", "PFRecShot"):
                    stats["FD"] += 1
                # PIR lo puedes calcular si quieres luego desde el boxscore ofensivo del rival

            # Al final del partido actual, puedes calcular el TR (total rebotes)
            stats["TR"] = stats["OR"] + stats["DR"]

    for team in team_names:
        stats = team_stats[team]
        FGM = stats["2PM"] + stats["3PM"]
        FGA = stats["2PA"] + stats["3PA"]
        missed_FG = FGA - FGM
        missed_FT = stats["FTA"] - stats["FTM"]

        PIR = (
            stats["FTM"]
            + stats["2PM"] * 2
            + stats["3PM"] * 3
            + stats["OR"]
            + stats["DR"]
            + stats["AST"]
            + stats["STL"]
            + stats["BLK"]
            + stats["FD"]
            - missed_FG
            - missed_FT
            - stats["TO"]
            - stats["FC"]
        )
        stats["PIR"] = PIR

    # Construimos el DataFrame
    rows = []
    for team in team_names:
        stats = team_stats[team]
        row = {"team_name": team}
        for field in stat_fields:
            row[f"{field}r"] = stats[field] if field in stats else 0
        rows.append(row)

    df_def = pd.DataFrame(rows)
    return df_def
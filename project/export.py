import pandas as pd
import csv
import os

def save_csv_players_total_box_score(box_scores):
    if not box_scores:
        print("⚠️ No hay datos para guardar.")
        return

    rows = []
    for item in box_scores:
        if item["player_name"] == "UNKNOWN":
            continue

        stats = item["stats"]

        # Asumimos que stats está en este orden:
        # ['#', 'GP', 'GS', 'Min', 'PTS', '2PM/A', '3PM/A', 'FTM/A', 'OR', 'DR', 'TR', 'AST', 'STL', 'TO', 'BLK', 'BLKA', 'FC', 'FD', 'PIR']

        # Extraemos y separamos los valores con "/"
        def split_m_a(value):
            if '/' in value:
                made, att = value.split('/')
                return made.strip(), att.strip()
            return value, ''

        two_pm, two_pa = split_m_a(stats[5])
        three_pm, three_pa = split_m_a(stats[6])
        ftm, fta = split_m_a(stats[7])

        row = [
            item["player_name"],  # Player
            stats[1],             # GP
            stats[2],             # GS
            stats[3],             # Min
            stats[4],             # PTS
            two_pm,               # 2PM
            two_pa,               # 2PA
            three_pm,             # 3PM
            three_pa,             # 3PA
            ftm,                  # FTM
            fta,                  # FTA
            stats[8],             # OR
            stats[9],             # DR
            stats[10],            # TR
            stats[11],            # AST
            stats[12],            # STL
            stats[13],            # TO
            stats[14],            # BLK
            stats[15],            # BLKA
            stats[16],            # FC
            stats[17],            # FD
            stats[18],            # PIR
        ]

        rows.append([item["team_name"]] + row)

    columns = [
        "team_name",
        "Player",
        "GP",
        "GS",
        "Min",
        "PTS",
        "2PM",
        "2PA",
        "3PM",
        "3PA",
        "FTM",
        "FTA",
        "OR",
        "DR",
        "TR",
        "AST",
        "STL",
        "TO",
        "BLK",
        "BLKA",
        "FC",
        "FD",
        "PIR",
    ]

    df = pd.DataFrame(rows, columns=columns)
    df.to_csv("./files/players_total_box_score.csv", index=False, encoding="utf-8-sig")
    print("✅ Archivo guardado: total_box_score.csv")

def save_csv_team_total_box_score(box_scores):
    if not box_scores:
        print("⚠️ No hay datos para guardar.")
        return

    rows = []
    for item in box_scores:
        if item["player_name"] == "UNKNOWN":
            continue

        stats = item["stats"]

        # Asumimos que stats está en este orden:
        # ['#', 'GP', 'GS', 'Min', 'PTS', '2PM/A', '3PM/A', 'FTM/A', 'OR', 'DR', 'TR', 'AST', 'STL', 'TO', 'BLK', 'BLKA', 'FC', 'FD', 'PIR']

        # Extraemos y separamos los valores con "/"
        def split_m_a(value):
            if '/' in value:
                made, att = value.split('/')
                return made.strip(), att.strip()
            return value, ''

        two_pm, two_pa = split_m_a(stats[5])
        three_pm, three_pa = split_m_a(stats[6])
        ftm, fta = split_m_a(stats[7])

        row = [
            stats[1],             # GP
            stats[3],             # Min
            stats[4],             # PTS
            two_pm,               # 2PM
            two_pa,               # 2PA
            three_pm,             # 3PM
            three_pa,             # 3PA
            ftm,                  # FTM
            fta,                  # FTA
            stats[8],             # OR
            stats[9],             # DR
            stats[10],            # TR
            stats[11],            # AST
            stats[12],            # STL
            stats[13],            # TO
            stats[14],            # BLK
            stats[15],            # BLKA
            stats[16],            # FC
            stats[17],            # FD
            stats[18],            # PIR
        ]

        rows.append([item["team_name"]] + row)

    columns = [
        "team_name",
        "GP",
        "Min",
        "PTS",
        "2PM",
        "2PA",
        "3PM",
        "3PA",
        "FTM",
        "FTA",
        "OR",
        "DR",
        "TR",
        "AST",
        "STL",
        "TO",
        "BLK",
        "BLKA",
        "FC",
        "FD",
        "PIR",
    ]

    df = pd.DataFrame(rows, columns=columns)
    df.to_csv("./files/team_total_box_score.csv", index=False, encoding="utf-8-sig")
    print("✅ Archivo guardado: total_box_score.csv")

def save_csv_team_defensive_box_score(df_defensive_stats: pd.DataFrame):
    
    filename = "team_total_box_scores_defensive.csv"
    base_dir = os.path.dirname(__file__)
    out_path = os.path.join(base_dir, "files", filename)
    df_defensive_stats.to_csv(out_path, index=False)


def save_csv_play_by_plays_raw(game_name, game_plays):
    if not game_plays:
        print("⚠️ No hay jugadas para guardar.")
        return

    df = pd.DataFrame(game_plays, columns=["local", "visitor", "period", "time", "player", "action", "side", "score_home", "score_away"])

    file_name = game_name.replace(" ", "_").replace("/", "-") + ".csv"
    path = f"./files/play_by_plays_raw/{file_name}"

    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"✅ Archivo guardado: {file_name}")

def save_csv_play_by_plays_clean(game_name, game_plays):
    if not game_plays:
        print("⚠️ No hay jugadas limpias para guardar.")
        return

    # Columnas base + 10 columnas para jugadores en pista
    fieldnames = [
        "period",
        "time",
        "player",
        "action_code",
        "side",
        "score_home",
        "score_away",
    ] + [f"homeplayer{i}" for i in range(1, 6)] + [f"awayplayer{i}" for i in range(1, 6)]

    file_name = game_name.replace(" ", "_").replace("/", "-") + ".csv"
    path = f"./files/play_by_plays/{file_name}"

    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for play in game_plays:
            home_players = sorted(play["players_on_court_home"])[:5]
            away_players = sorted(play["players_on_court_away"])[:5]

            row = {
                "period": play["period"],
                "time": play["time"],
                "player": play["player"],
                "action_code": play["action_code"],
                "side": play["side"],
                "score_home": play["score_home"],
                "score_away": play["score_away"],
            }

            # Añadir jugadores de home y away, rellena vacíos si hay menos de 5
            for i in range(5):
                row[f"homeplayer{i+1}"] = home_players[i] if i < len(home_players) else ""
                row[f"awayplayer{i+1}"] = away_players[i] if i < len(away_players) else ""

            writer.writerow(row)

    print(f"✅ Archivo CSV guardado en: {path}")

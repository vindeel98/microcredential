from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

from config.utils import ACTION_CODES

from config.urls import ANGT_GAMES, ANGT_TEAMS, BOX_SCORE_ENDPOINT, PLAY_BY_PLAY_ENDPOINT

def scrap_urls_games(tournament_id):
    round_number = 1
    results = []
    previous_final_url = None

    service = Service("./config/chromedriver.exe")
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)

    while True:
        url = ANGT_GAMES.format(tournament=tournament_id, round=round_number)
        print(f"\nAbriendo {url}")
        driver.get(url)

        # Esperar redirección y contenido correcto
        try:
            WebDriverWait(driver, 10).until(lambda d: tournament_id.lower() in d.current_url.lower())
        except:
            print("Redirección no completada o URL inesperada. Fin.")
            break

        # Esperar a que haya al menos 1 link con href válido
        try:
            WebDriverWait(driver, 10).until(
                lambda d: any(
                    link.get_attribute("href") and tournament_id.lower() in link.get_attribute("href").lower()
                    for link in d.find_elements(By.CSS_SELECTOR, "a[href*='/es/ngt/game-center/']")
                )
            )
        except:
            print(f"No se encontraron partidos válidos en round {round_number}. Fin.")
            break

        final_url = driver.current_url
        if final_url == previous_final_url:
            print(f"URL final repetida: {final_url}. Fin del scraping.")
            break
        previous_final_url = final_url

        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/es/ngt/game-center/']")
        count = 0
        for a in links:
            href = a.get_attribute("href")
            if not href or tournament_id.lower() not in href.lower():
                continue  # Saltar enlaces incompletos o basura

            try:
                span = a.find_element(By.TAG_NAME, "span")
                title = span.text.strip()
            except:
                title = "Partido sin título"

            results.append((title, href))
            print((title, href))
            count += 1

        print(f"Scrapeados {count} partidos en round {round_number}.")
        round_number += 1

    driver.quit()
    return results

def scrap_urls_teams(tournament_id):
    service = Service("./config/chromedriver.exe")
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)

    url = ANGT_TEAMS
    driver.get(url)

    # Espera a que aparezca el selector de torneo
    select_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "select.teams-select_select__Xa4cE"))
    )

    # Guarda el primer equipo actual (para detectar el cambio tras seleccionar)
    initial_first_team = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.teams-card_card__NYdFB span.teams-card_name__UR_gA"))
    ).text.strip()

    # Cambia el torneo con el selector
    select = Select(select_element)
    select.select_by_value(tournament_id)

    # Espera hasta que el primer equipo sea diferente (cambio real de contenido)
    WebDriverWait(driver, 10).until(
        lambda d: d.find_element(By.CSS_SELECTOR, "a.teams-card_card__NYdFB span.teams-card_name__UR_gA").text.strip() != initial_first_team
    )

    # Una vez cambiado, volvemos a encontrar todos los equipos nuevos
    team_cards = driver.find_elements(By.CSS_SELECTOR, "a.teams-card_card__NYdFB")

    results = []
    for team in team_cards:
        try:
            href = team.get_attribute("href")
            name = team.find_element(By.CSS_SELECTOR, "span.teams-card_name__UR_gA").text.strip()
            results.append((name, href))
            print(name, href)
        except Exception as e:
            print("Error leyendo equipo:", e)

    driver.quit()
    return results

def scrap_box_scores(teams_urls):
    service = Service("./config/chromedriver.exe")
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)

    all_stats = []

    for team in teams_urls:
        team_name, team_url = team
        stats_url = team_url.replace("roster", "statistics") + "&" + BOX_SCORE_ENDPOINT
        print(f"🔍 Visitando: {stats_url}")
        driver.get(stats_url)

        try:
            WebDriverWait(driver, 15).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "div.complex-stat-table_row__XPRhI[role='row']")) > 5
            )

            time.sleep(2)  # Espera adicional para asegurar que la tabla esté completamente renderizada

            rows = driver.find_elements(By.CSS_SELECTOR, "div.complex-stat-table_row__XPRhI[role='row']")

            for row in rows:
                cells = row.find_elements(By.CSS_SELECTOR, "p.complex-stat-table_cell__XIEO5")
                if not cells or all(cell.text.strip() == "" for cell in cells):
                    continue

                try:
                    name_container = row.find_element(By.CSS_SELECTOR, "div[role='cell'][title]")
                    player_name = name_container.get_attribute("title").strip()
                except:
                    player_name = "UNKNOWN"

                if player_name == "UNKNOWN":
                    continue  # ❌ Saltamos jugadores sin nombre

                stats = [cell.text.strip() for cell in cells]

                player_stats = {
                    "team_name": team_name,
                    "player_name": player_name,
                    "stats": stats
                }

                print(player_stats)
                all_stats.append(player_stats)

        except Exception as e:
            print(f"⚠️ Error en {stats_url}: {e}")

    driver.quit()
    return all_stats

def scrap_play_by_plays(game_url):
    service = Service("./config/chromedriver.exe")
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Descomenta para modo headless
    driver = webdriver.Chrome(service=service, options=options)

    plays = []

    driver.get(game_url + "/#" + PLAY_BY_PLAY_ENDPOINT )

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.play-by-play-buttons-list_button__wkQqw"))
        )

        # Cerrar cookies si aparece
        try:
            WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            ).click()
        except:
            pass

        time.sleep(2)

        # Obtener nombres de equipos
        try:
            home = driver.find_element(By.CSS_SELECTOR, ".play-by-play-final-score_team__gIR7R:nth-child(1) img").get_attribute("alt").strip()
            visitor = driver.find_element(By.CSS_SELECTOR, ".play-by-play-final-score_team__gIR7R:nth-child(3) img").get_attribute("alt").strip()
        except:
            home, visitor = "home", "visitor"

        
        buttons = [
            btn for btn in driver.find_elements(By.CSS_SELECTOR, "button.play-by-play-buttons-list_button__wkQqw")
            if btn.is_enabled()
        ]

        for btn in buttons:
            period = btn.text.strip()
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(2)

            rows = driver.find_elements(By.CSS_SELECTOR, "ul.play-by-play-content-list_list__IAELd > li")
            score_home, score_away = "", ""

            for row in rows:
                play = {
                    "local": home,
                    "visitor": visitor,
                    "period": period,
                    "time": None,
                    "player": None,
                    "action": None,
                    "side": None,
                    "score_home": score_home,
                    "score_away": score_away
                }

                # 🟥 Jugada con bloque EXTENSIVO (anota)
                try:
                    block = row.find_element(By.CSS_SELECTOR, "div.play-by-play-content-list-item-extensive_block__ZBIPh")

                    play["score_home"] = block.find_elements(By.CSS_SELECTOR, "p.play-by-play-score-stats_statsItemText__NKUQq")[0].text.strip()
                    play["score_away"] = block.find_elements(By.CSS_SELECTOR, "p.play-by-play-score-stats_statsItemText__NKUQq")[1].text.strip()
                    play["time"] = block.find_element(By.CSS_SELECTOR, "span.play-by-play-content-list-item-extensive_timeText__3qSiy").text.strip()

                    for side_css, side_label in [("right", visitor), ("left", home)]:
                        try:
                            text_block = block.find_element(By.CSS_SELECTOR, "[class*='textBlock_right']")
                            play["player"] = text_block.find_element(By.CSS_SELECTOR, "p.play-by-play-info-text_name__dTOhQ").text.strip()
                            play["action"] = text_block.find_element(By.CSS_SELECTOR, "p.play-by-play-info-text_stat__vapMZ").text.strip()
                            play["side"] = visitor
                        except NoSuchElementException:
                            try:
                                text_block = block.find_element(By.CSS_SELECTOR, "[class*='textBlock_left']")
                                play["player"] = text_block.find_element(By.CSS_SELECTOR, "p.play-by-play-info-text_name__dTOhQ").text.strip()
                                play["action"] = text_block.find_element(By.CSS_SELECTOR, "p.play-by-play-info-text_stat__vapMZ").text.strip()
                                play["side"] = home
                            except NoSuchElementException:
                                pass
                    print(play)
                    plays.append(play)
                    continue
                except:
                    pass

                # 🟨 Jugada SIMPLE sin anotación
                try:
                    block = row.find_element(By.CSS_SELECTOR, "div.play-by-play-content-list-item_block__zk9Ab")

                    # Tiempo
                    try:
                        play["time"] = block.find_element(By.CSS_SELECTOR, "span.play-by-play-content-list-item_timeText__Ye2xJ").text.strip()
                    except:
                        pass

                    try:
                        # Intentar RIGHT
                        text_block = block.find_element(By.CSS_SELECTOR, "[class*='textBlock_right']")
                        play["player"] = text_block.find_element(By.CSS_SELECTOR, "p.play-by-play-info-text_name__dTOhQ").text.strip()
                        play["action"] = text_block.find_element(By.CSS_SELECTOR, "p.play-by-play-info-text_stat__vapMZ").text.strip()
                        play["side"] = visitor
                    except NoSuchElementException:
                        try:
                            # Intentar LEFT
                            text_block = block.find_element(By.CSS_SELECTOR, "[class*='textBlock_left']")
                            play["player"] = text_block.find_element(By.CSS_SELECTOR, "p.play-by-play-info-text_name__dTOhQ").text.strip()
                            play["action"] = text_block.find_element(By.CSS_SELECTOR, "p.play-by-play-info-text_stat__vapMZ").text.strip()
                            play["side"] = home
                        except NoSuchElementException:
                            pass
                    print(play)
                    plays.append(play)
                except:
                    continue

    except Exception as e:
        print(f"❌ Error al procesar {game_url}: {e}")

    driver.quit()
    return plays

def clean_play_by_plays(play_by_plays):
    cleaned = []
    quarters = {}
    last_known_score = {"home": "0", "away": "0"}
    players_on_court = {"home": [], "away": []}

    # Agrupar por cuarto
    for play in play_by_plays:
        quarters.setdefault(play["period"], []).append(play)

    period_map = {
        "1er Cuarto": 1,
        "2º Cuarto": 2,
        "3er Cuarto": 3,
        "4º Cuarto": 4,
        "Prórroga": 5,
    }

    for period_name in sorted(quarters.keys(), key=lambda x: period_map.get(x, 99)):
        period_number = period_map.get(period_name, period_name)
        period_plays = list(reversed(quarters[period_name]))

        local_team = period_plays[0]["local"]
        visitor_team = period_plays[0]["visitor"]

        # Reiniciar score y quintetos solo en primer cuarto
        if period_number == 1:
            last_known_score = {"home": "0", "away": "0"}
            players_on_court = {"home": [], "away": []}

        i = 0
        while i < len(period_plays):
            play = period_plays[i]
            side = "home" if play["side"] == local_team else "away"
            opponent = "away" if side == "home" else "home"

            player = play["player"]
            action = play["action"] or ""
            score_home_play = play["score_home"]
            score_away_play = play["score_away"]

            # Actualizar marcador si hay datos
            if score_home_play:
                last_known_score["home"] = score_home_play
            if score_away_play:
                last_known_score["away"] = score_away_play

            # Mapear acción a código (preferencia por coincidencias más largas)
            action_code = None
            for key in sorted(ACTION_CODES.keys(), key=len, reverse=True):
                if key in action:
                    action_code = ACTION_CODES[key]
                    break
            if not action_code:
                action_code = "UNKNOWN"

            # Si no hay jugador pero hay acción, poner TEAM
            if not player:
                player = "TEAM"

            # Manejar sustituciones (no se añaden al cleaned)
            if action_code == "IN":
                if player not in players_on_court[side]:
                    players_on_court[side].append(player)
                i += 1
                continue
            elif action_code == "OUT":
                if player in players_on_court[side]:
                    players_on_court[side].remove(player)
                i += 1
                continue

            # Detectar PFRec → PFRecShot si siguiente jugada es FTM o FTA del mismo jugador
            if action_code == "PFRec" and i + 1 < len(period_plays):
                next_play = period_plays[i + 1]
                next_action = next_play["action"] or ""
                next_player = next_play["player"]

                for key in sorted(ACTION_CODES.keys(), key=len, reverse=True):
                    if key in next_action:
                        next_code = ACTION_CODES[key]
                        break
                else:
                    next_code = "UNKNOWN"

                if next_code in {"FTM", "FTA"} and next_player == player:
                    action_code = "PFRecShot"

            # Acción normal → considerar jugador como en pista
            if player and player not in players_on_court[side] and player != "TEAM":
                if len(players_on_court[side]) < 5:
                    players_on_court[side].append(player)
                    # Añadir retroactivamente
                    for prev_play in reversed(cleaned):
                        if prev_play["period"] == period_number and len(prev_play[f"players_on_court_{side}"]) < 5:
                            prev_play[f"players_on_court_{side}"].append(player)

            # Omitir jugadas TEAM + UNKNOWN
            if player == "TEAM" and action_code == "UNKNOWN":
                i += 1
                continue

            cleaned_play = {
                "period": period_number,
                "time": play["time"],
                "player": player,
                "action_code": action_code,
                "side": play["side"],
                "score_home": last_known_score["home"],
                "score_away": last_known_score["away"],
                "players_on_court_home": list(players_on_court["home"]),
                "players_on_court_away": list(players_on_court["away"]),
            }

            cleaned.append(cleaned_play)
            i += 1

    return cleaned

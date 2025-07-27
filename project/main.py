from config.utils import TOURNAMENT_IDENTIFIERS
import export
import scrap
import team_stats
import player_stats

def main():

    tournament = TOURNAMENT_IDENTIFIERS["ANGT_2025_BELGRADE"]

    ## BOX SCORE SRAPING

    teams_urls = scrap.scrap_urls_teams(tournament)
    players_box_scores, team_box_scores = scrap.scrap_box_scores(teams_urls)
    export.save_csv_players_total_box_score(players_box_scores)
    export.save_csv_team_total_box_score(team_box_scores)

    ## PLAY BY PLAY SCRAPING
    
    games_urls = scrap.scrap_urls_games(tournament)
    for game_name, game_url in games_urls:
        play_by_plays = scrap.scrap_play_by_plays(game_url=game_url)
        export.save_csv_play_by_plays_raw(game_name= game_name, game_plays=play_by_plays)
        
        print("----")

        cleaned_play_by_plays = scrap.clean_play_by_plays(play_by_plays)
        export.save_csv_play_by_plays_clean(game_name=game_name,game_plays=cleaned_play_by_plays)
    

    ## BOX SCORE AGAINST ME
    
    team_box_scores_defensive = team_stats.get_team_defensive_stats_from_play_by_plays(
        play_by_play_folder="files/play_by_plays",
        team_list_csv="files/team_total_box_score.csv"
    )
    export.save_csv_team_defensive_box_score(team_box_scores_defensive)
    

    # REPORT GENERATING

    team_name = "U18 EA7 Emporio Armani Milan"

    team_stats.scout_team(
        team_name=team_name,
        offensive_csv_path="files/team_total_box_score.csv",
        defensive_csv_path="files/team_total_box_scores_defensive.csv"
    )
    
    player_stats.scout_team(
        team_name=team_name,
        offensive_csv_path="files/team_total_box_score.csv",
        defensive_csv_path="files/team_total_box_scores_defensive.csv",
        players_csv_path="files/players_total_box_score.csv"
    )


    ## TESTING
    
    #games_urls = scrap.scrap_urls_games(tournament)
    #play_by_plays = scrap.scrap_play_by_plays(game_url="https://www.euroleaguebasketball.net/es/ngt/game-center/2024-2025-belgrade/u18-crvena-zvezda-belgrade-u18-maccabi-tel-aviv/JTB24/1/")
    #export.save_csv_play_by_plays_raw(game_name= "game_U18_Maccabi_Tel_Aviv_vs_U18_Crvena_Zvezda_Belgrade", game_plays=play_by_plays)

    #print("----")

    #cleaned_play_by_plays = scrap.clean_play_by_plays(play_by_plays)
    #export.save_csv_play_by_plays_clean(game_name="game_U18_Maccabi_Tel_Aviv_vs_U18_Crvena_Zvezda_Belgrade",game_plays=cleaned_play_by_plays)
    
if __name__ == "__main__":
    main()
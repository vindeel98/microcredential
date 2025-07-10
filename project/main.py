from config.utils import TOURNAMENT_IDENTIFIERS
import export
import scrap

def main():
    tournament = TOURNAMENT_IDENTIFIERS["ANGT_2025_BELGRADE"]

    ## BOX SCORE SRAPING

    #teams_urls = scrap.scrap_urls_teams(tournament)
    #box_scores = scrap.scrap_box_scores(teams_urls)
    #save_csv_total_box_score(box_scores)

    ## PLAY BY PLAY SCRAPING
    
    games_urls = scrap.scrap_urls_games(tournament)
    for game_name, game_url in games_urls:
        play_by_plays = scrap.scrap_play_by_plays(game_url=game_url)
        export.save_csv_play_by_plays_raw(game_name= game_name, game_plays=play_by_plays)
        
        print("----")

        cleaned_play_by_plays = scrap.clean_play_by_plays(play_by_plays)
        export.save_csv_play_by_plays_clean(game_name=game_name,game_plays=cleaned_play_by_plays)
    

    ## TESTING
    
    #games_urls = scrap.scrap_urls_games(tournament)
    #play_by_plays = scrap.scrap_play_by_plays(game_url="https://www.euroleaguebasketball.net/es/ngt/game-center/2024-2025-belgrade/u18-crvena-zvezda-belgrade-u18-maccabi-tel-aviv/JTB24/1/")
    #export.save_csv_play_by_plays_raw(game_name= "game_U18_Maccabi_Tel_Aviv_vs_U18_Crvena_Zvezda_Belgrade", game_plays=play_by_plays)

    #print("----")

    #cleaned_play_by_plays = scrap.clean_play_by_plays(play_by_plays)
    #export.save_csv_play_by_plays_clean(game_name="game_U18_Maccabi_Tel_Aviv_vs_U18_Crvena_Zvezda_Belgrade",game_plays=cleaned_play_by_plays)
    
if __name__ == "__main__":
    main()
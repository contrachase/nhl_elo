import pandas as pd
import random
import csv
import os.path
from utilities_season_elo import calculate_seasons_elo, go_back_in_time
from converters import make_teams_to_franchises, make_franchises_to_names
from elo_calculations import win_probability, update_elo
from playoffs import play_the_playoffs

def simulate_seasons(seasonid, n, verbose = False, percent = False, write_to_file = True) :
    if verbose :
        season_simmed = seasonid
        print(f"simulating {season_simmed}")
        
    teams_to_franchises = make_teams_to_franchises()
    franchises_to_names = make_franchises_to_names()

    start_season = go_back_in_time(seasonid, 10)
    end_season = go_back_in_time(seasonid, 1)
    elos_df, seasons_df = calculate_seasons_elo(start_season, end_season)
    
    elos_dict = dict(zip(elos_df['franchiseId'], elos_df['eloRating']))

    expansion_ids = [a for a in seasons_df[seasonid]['homeFranchiseId'].unique() if not a in seasons_df[end_season]['homeFranchiseId'].unique()]

    for team in expansion_ids :
        elos_dict[team] = 1200
    
    original_elos_dict = elos_dict.copy()

    season_games = seasons_df[seasonid]

    stanley_dict = {id: 0 for id in elos_dict.keys()}
    playoffs_dict = {id: 0 for id in elos_dict.keys()}

    for i in range(n):
        elos_dict = original_elos_dict.copy()
        season_games['homeFranchiseId'] = season_games['homeTeamId'].map(teams_to_franchises)
        season_games['visitingFranchiseId'] = season_games['visitingTeamId'].map(teams_to_franchises)

        season_games['homeElo'] = season_games['homeFranchiseId'].map(elos_dict)
        season_games['visitingElo'] = season_games['visitingFranchiseId'].map(elos_dict)

        points_dict = {id: 0 for id in elos_dict.keys()}

        for index, game in season_games.iterrows():
            home_elo = elos_dict[game['homeFranchiseId']]
            visiting_elo = elos_dict[game['visitingFranchiseId']]
            
            home_win_prob = win_probability(home_elo, visiting_elo)[0]

            if random.random() < home_win_prob :
                home_result = 1
                visiting_result = 0
            else :
                home_result = 0
                visiting_result = 1

            points_dict[game['homeFranchiseId']] += home_result * 2 if home_result == 1 else int(random.random()<.25)
            points_dict[game['visitingFranchiseId']] += visiting_result * 2 if visiting_result == 1 else int(random.random()<.25)

            elos_dict[game['homeFranchiseId']], elos_dict[game['visitingFranchiseId']] = update_elo(home_elo, visiting_elo, home_result)
        
        end_of_season_elos = pd.DataFrame({'franchiseId': list(elos_dict.keys()), 'eloRating': list(elos_dict.values())})
        end_of_season_points = pd.DataFrame({'franchiseId': list(points_dict.keys()), 'points': list(points_dict.values())})

        merged_df = end_of_season_elos.merge(end_of_season_points).sort_values(by='points', ascending=False )
        merged_df = merged_df.reset_index(drop=True)

        playoff_results = play_the_playoffs(merged_df)
        scw = playoff_results.loc[playoff_results['inPlayoffs'] == 5, 'franchiseId'].iloc[0]


        for index, row in playoff_results.iterrows() :
            playoffs_dict[row['franchiseId']] += 1
            if row['inPlayoffs'] == 5: 
                stanley_dict[row['franchiseId']] += 1
        
        if verbose :
            print(i, franchises_to_names[scw])

        if write_to_file:
            field_names = [key for key in stanley_dict.keys()]
            file_path = f'simulations/{seasonid}_simulations.csv'

            dict_to_add = dict(zip(playoff_results['franchiseId'].astype(int), playoff_results['inPlayoffs']))

            for team in elos_dict :
                if team not in dict_to_add :
                    dict_to_add[team] = 0

            with open(file_path, 'a+') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=field_names)
                try:
                    file_size = os.path.getsize(file_path)
                except FileNotFoundError:
                    file_size = 0

                if file_size == 0:
                    writer.writeheader()

                writer.writerow(dict_to_add)
    
    if percent :
        stanley_dict = {key: f"{value*100/n}%" for key, value in stanley_dict.items()}
        playoffs_dict = {key: f"{value*100/n}%" for key, value in playoffs_dict.items()}

    cups_df = pd.DataFrame.from_dict(stanley_dict, orient='index', columns=['cups']).reset_index().rename(
        columns={'index': 'franchiseId'})
    cups_df = cups_df.sort_values(by='cups', ascending=False)
    playoffs_df = pd.DataFrame.from_dict(playoffs_dict, orient='index', columns=['playoffAppearences']).reset_index().rename(
        columns={'index': 'franchiseId'})
    playoffs_df = playoffs_df.sort_values(by='playoffAppearences', ascending=False)
    cups_and_playoffs = cups_df.merge(playoffs_df).sort_values(by='cups', ascending=False)
    cups_and_playoffs = cups_and_playoffs.sort_values(by='cups', ascending=False)
    cups_and_playoffs = cups_and_playoffs.reset_index(drop=True)
            
    return cups_and_playoffs

def main() :
    df = simulate_seasons(20242025, 1000, verbose = True, write_to_file = True)

    print(df)

if __name__ == '__main__' :
    main()
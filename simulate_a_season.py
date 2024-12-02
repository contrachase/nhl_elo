import pandas as pd
import random
from utilities_season_elo import calculate_seasons_elo, go_back_in_time
from converters import make_teams_to_franchises, make_franchises_to_names
from elo_calculations import win_probability, update_elo

def simulate_an_old_season(seasonid, next_season = False, verbose = False) :
    teams_to_franchises = make_teams_to_franchises()

    start_season = go_back_in_time(seasonid, 10)
    end_season = go_back_in_time(seasonid, 1) if not next_season else seasonid
    elos_df, seasons_df = calculate_seasons_elo(start_season, end_season)

    elos_dict = dict(zip(elos_df['franchiseId'], elos_df['eloRating']))

    expansion_ids = [
        team for team in seasons_df[seasonid]['homeFranchiseId'].unique() 
        if team not in seasons_df[end_season]['homeFranchiseId'].unique()
    ]
    
    for team in expansion_ids :
        elos_dict[team] = 1200

    season_games = seasons_df[seasonid]

    season_games['homeFranchiseId'] = season_games['homeTeamId'].map(teams_to_franchises)
    season_games['visitingFranchiseId'] = season_games['visitingTeamId'].map(teams_to_franchises)

    season_games['homeElo'] = season_games['homeFranchiseId'].map(elos_dict)
    season_games['visitingElo'] = season_games['visitingFranchiseId'].map(elos_dict)

    points_dict = {id: 0 for id in elos_dict.keys()}

    for index, game in season_games.iterrows():
        home_elo = elos_dict[game['homeFranchiseId']]
        visiting_elo = elos_dict[game['visitingFranchiseId']]
        
        home_win_prob = win_probability(home_elo, visiting_elo)[0]

        if random.random() < home_win_prob:
            home_result, visiting_result = 1, 0
        else:
            home_result, visiting_result = 0, 1

        points_dict[game['homeFranchiseId']] += home_result * 2 if home_result == 1 else int(random.random()<.25)
        points_dict[game['visitingFranchiseId']] += visiting_result * 2 if visiting_result == 1 else int(random.random()<.25)

        elos_dict[game['homeFranchiseId']], elos_dict[game['visitingFranchiseId']] = update_elo(home_elo, visiting_elo, home_result)

    end_of_season_elos = pd.DataFrame({'franchiseId': list(elos_dict.keys()), 'eloRating': list(elos_dict.values())})
    end_of_season_points = pd.DataFrame({'franchiseId': list(points_dict.keys()), 'points': list(points_dict.values())})

    merged_df = end_of_season_elos.merge(end_of_season_points).sort_values(by='points', ascending=False )
    merged_df = merged_df.reset_index(drop=True)

    return merged_df.reset_index(drop=True)

def main() :
    df = simulate_an_old_season(20062007)
    df['teamName'] = df['franchiseId'].map(make_franchises_to_names())
    print(df)

if __name__ == '__main__' :
    main()
import pandas as pd
from utilities_season_elo import calculate_seasons_elo, go_back_in_time, get_game_df
from converters import make_teams_to_franchises, make_franchises_to_names
from elo_calculations import update_elo
from playoffs import make_playoff_info, play_the_playoffs

def get_end_of_season_stats(seasonid) :
    teams_to_franchises = make_teams_to_franchises()

    start_season = go_back_in_time(seasonid, 10)
    end_season = seasonid
    elos_df, seasons_df = calculate_seasons_elo(start_season, end_season)

    elos_dict = dict(zip(elos_df['franchiseId'], elos_df['eloRating']))

    expansion_ids = [a for a in seasons_df[seasonid]['homeFranchiseId'].unique() if not a in seasons_df[end_season]['homeFranchiseId'].unique()]
    
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
        
        if game['homeResult'] == 1:
            # Home team wins (regulation, OT, or shootout)
            points_dict[game['homeFranchiseId']] += 2
            if game['period'] > 3:
                # Visiting team wins in OT or shootout
                points_dict[game['visitingFranchiseId']] += 1  # OT loss point for home team

        elif game['homeResult'] == 0:
            points_dict[game['visitingFranchiseId']] += 2
            if game['period'] > 3:
                # Visiting team wins in OT or shootout
                points_dict[game['homeFranchiseId']] += 1  # OT loss point for home team
                
        elos_dict[game['homeFranchiseId']], elos_dict[game['visitingFranchiseId']] = update_elo(home_elo, visiting_elo, game['homeResult'])

    end_of_season_elos = pd.DataFrame({'franchiseId': list(elos_dict.keys()), 'eloRating': list(elos_dict.values())})
    end_of_season_points = pd.DataFrame({'franchiseId': list(points_dict.keys()), 'points': list(points_dict.values())})

    merged_df = end_of_season_elos.merge(end_of_season_points).sort_values(by='points', ascending=False )
    merged_df = merged_df.reset_index(drop=True)

    return merged_df.reset_index(drop=True)

def get_playoff_games():
    game_df = get_game_df()
    # Filter games where 'gameType' equals 2
    filtered_df = game_df[(game_df['gameType'] == 3)]

    # Group the filtered DataFrame by the 'season' column
    grouped = filtered_df.groupby('season')

    # Create an empty dictionary to store DataFrames for each season
    season_dfs = {}

    # Iterate over the groups and store each DataFrame in the dictionary
    for season, group_df in grouped:
        season_dfs[season] = group_df

    return season_dfs

def simulate_current_playoffs_20232024():
    end_of_season_stats = get_end_of_season_stats(20232024)
    
    # Convert the points column to float to avoid dtype issues
    end_of_season_stats['points'] = end_of_season_stats['points'].astype(float)
    
    end_of_season_stats.loc[end_of_season_stats['franchiseId'] == 24.0, 'points'] += 0.5
    playoffs = play_the_playoffs(end_of_season_stats)

    playoff_games = get_playoff_games()[20232024]
    print(playoff_games)

    return playoffs

def main() :
    df = get_end_of_season_stats(20232024)
    df['teamName'] = df['franchiseId'].map(make_franchises_to_names())

    simulate_current_playoffs_20232024()

if __name__ == '__main__' :
    main()
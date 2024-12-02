import json
import pandas as pd
from elo_calculations import update_elo
from converters import make_teams_to_franchises

def all_seasons_list() :
    return [
    19171918,
    19181919,
    19191920,
    19201921,
    19211922,
    19221923,
    19231924,
    19241925,
    19251926,
    19261927,
    19271928,
    19281929,
    19291930,
    19301931,
    19311932,
    19321933,
    19331934,
    19341935,
    19351936,
    19361937,
    19371938,
    19381939,
    19391940,
    19401941,
    19411942,
    19421943,
    19431944,
    19441945,
    19451946,
    19461947,
    19471948,
    19481949,
    19491950,
    19501951,
    19511952,
    19521953,
    19531954,
    19541955,
    19551956,
    19561957,
    19571958,
    19581959,
    19591960,
    19601961,
    19611962,
    19621963,
    19631964,
    19641965,
    19651966,
    19661967,
    19671968,
    19681969,
    19691970,
    19701971,
    19711972,
    19721973,
    19731974,
    19741975,
    19751976,
    19761977,
    19771978,
    19781979,
    19791980,
    19801981,
    19811982,
    19821983,
    19831984,
    19841985,
    19851986,
    19861987,
    19871988,
    19881989,
    19891990,
    19901991,
    19911992,
    19921993,
    19931994,
    19941995,
    19951996,
    19961997,
    19971998,
    19981999,
    19992000,
    20002001,
    20012002,
    20022003,
    20032004,
    20052006,
    20062007,
    20072008,
    20082009,
    20092010,
    20102011,
    20112012,
    20122013,
    20132014,
    20142015,
    20152016,
    20162017,
    20172018,
    20182019,
    20192020,
    20202021,
    20212022,
    20222023,
    20232024,
    20242025
]

def split_df_by_season(df, include_playoffs=False):
    game_types = [2]
    if include_playoffs:
        game_types.append(3)
    return {season: group_df for season, group_df in df[df['gameType'].isin(game_types)].groupby('season')}

def adjust_back(elos):
    return {team: int(0.7 * elo + 0.3 * 1600) for team, elo in elos.items()}

def go_back_in_time( seasonid, how_far ) :
    all_seasons = all_seasons_list()
    return all_seasons[all_seasons.index(seasonid) - how_far]

def get_all_seasons_between( startingid, endingid) :
    all_seasons = all_seasons_list()
    return all_seasons[all_seasons.index(startingid): all_seasons.index(endingid) + 1]

def get_game_df() :
    franchise_converter = make_teams_to_franchises()
    with open('all_games.json', 'r') as f:
        game_data = json.load(f)
    game_df = pd.DataFrame(game_data['data'])

    game_df['homeFranchiseId'] = game_df['homeTeamId'].map(franchise_converter)
    game_df['visitingFranchiseId'] = game_df['visitingTeamId'].map(franchise_converter)

    return game_df

def calculate_seasons_elo(start_season, end_season, include_playoffs = False):
    seasons_between = get_all_seasons_between(start_season, end_season)
    game_df = get_game_df()
    season_dfs = split_df_by_season(game_df, include_playoffs)

    starting_ids = season_dfs[start_season]['homeFranchiseId'].unique()
    ending_ids = season_dfs[end_season]['homeFranchiseId'].unique()
    expansion_ids = [a for a in season_dfs[start_season]['homeFranchiseId'].unique() if not a in season_dfs[go_back_in_time(start_season,1)]['homeFranchiseId'].unique()]

    # Initialize Elo ratings for each franchises
    franchise_elos = {franchise_id: 1500 for franchise_id in starting_ids}
    expansion_elos = {expansion_id: 1200 for expansion_id in expansion_ids}
    franchise_elos = franchise_elos | expansion_elos

    # Iterate over the seasons to calculate Elo ratings
    for season_id in seasons_between:
        season_df = season_dfs[season_id]
        
        if seasons_between.index(season_id) != 0 :
            adjust_back(franchise_elos)
            expansion_ids = [a for a in season_dfs[season_id]['homeFranchiseId'].unique() if not a in season_dfs[go_back_in_time(season_id,1)]['homeFranchiseId'].unique()]
            expansion_elos = {expansion_id: 1200 for expansion_id in expansion_ids}
            franchise_elos = franchise_elos | expansion_elos

        #season_df['homeResult'] = 0
        win_mask = season_df['homeScore'] > season_df['visitingScore']
        loss_mask = (season_df['homeScore'] < season_df['visitingScore'])

        season_df.loc[win_mask, 'homeResult'] = 1  # Set wins to 1
        season_df.loc[loss_mask, 'homeResult'] = 0  # Set losses to 0

        # Update Elo ratings
        for index, game in season_df.iterrows():
            home_franchise = game['homeFranchiseId']
            visiting_franchise = game['visitingFranchiseId']
            home_result = game['homeResult']
            franchise_elos[home_franchise], franchise_elos[visiting_franchise] = update_elo(franchise_elos[home_franchise], franchise_elos[visiting_franchise], home_result)

    franchise_elos = {key: value for key, value in franchise_elos.items() if key in ending_ids}
    end_of_season_df = pd.DataFrame({'franchiseId': list(franchise_elos.keys()), 'eloRating': list(franchise_elos.values())})
    end_of_season_df = end_of_season_df.sort_values(by='eloRating', ascending=False )
    return end_of_season_df, season_dfs
import random
import pandas as pd
from elo_calculations import win_probability, update_elo
from converters import make_teams_to_franchises, make_franchises_to_names
from simulate_a_season import simulate_an_old_season
from pprint import pprint

def get_divisions():
    return {
        1: 'met', 2: 'met', 3: 'met', 4: 'met', 5: 'met',
        6: 'atl', 7: 'atl', 8: 'atl', 9: 'atl', 10: 'atl',
        12: 'met', 13: 'atl', 14: 'atl', 15: 'met',
        16: 'cen', 17: 'atl', 18: 'cen', 19: 'cen',
        20: 'pac', 21: 'cen', 22: 'pac', 23: 'pac', 24: 'pac',
        25: 'cen', 26: 'pac', 28: 'pac', 29: 'met', 30: 'cen',
        52: 'cen', 53: 'cen', 54: 'pac', 55: 'pac', 13: 'atl',
        40: 'cen'
    }

def initialize_playoff_info(standings_dict, franchise_divisions):
    sorted_standings = sorted(standings_dict.items(), key=lambda item: (item[1], random.random()), reverse=True)
    return [
        {
            'franchiseId': team,
            'points': points,
            'division': franchise_divisions[team],
            'seed': None,
            'opponent': None,
            'place': index,
            'conferenceWinner': 0
        }
        for index, (team, points) in enumerate(sorted_standings)
    ]

def assign_seeds(divisions):
    for division in divisions:
        for i in range(3):
            division[i]['seed'] = f"{division[i]['division'][:3]}{i + 1}"

def determine_conference_winners(eastern_playoffs, western_playoffs):
    eastern_playoffs[0]['conferenceWinner'] = 1
    western_playoffs[0]['conferenceWinner'] = 1

def assign_wild_card_seeds(playoffs, conference_prefix):
    seeds = [f'{conference_prefix}1', f'{conference_prefix}2']
    for team in playoffs:
        if 'ewc' not in str(team['seed']) and team['seed'] is None:
            for seed in seeds:
                if seed not in [t['seed'] for t in playoffs]:
                    team['seed'] = seed
                    break

def set_opponents(playoffs, seed1, seed2, seed_opponent1, seed_opponent2):
    for team in playoffs:
        if team['opponent'] is None:
            if team['seed'] == seed1 and team['conferenceWinner'] == 1:
                opponent = next(t for t in playoffs if t['seed'] == seed_opponent2)
                team['opponent'] = opponent['franchiseId']
                opponent['opponent'] = team['franchiseId']
            elif team['seed'] == seed1:
                opponent = next(t for t in playoffs if t['seed'] == seed_opponent1)
                team['opponent'] = opponent['franchiseId']
                opponent['opponent'] = team['franchiseId']
            elif team['seed'] == seed2:
                opponent = next(t for t in playoffs if t['seed'] == f'{seed2[:3]}3')
                team['opponent'] = opponent['franchiseId']
                opponent['opponent'] = team['franchiseId']

def make_playoff_info(standings_df):
    standings_dict = standings_df.set_index('franchiseId')['points'].to_dict()
    converter = make_teams_to_franchises()
    divisions = get_divisions()
    franchise_divisions = {converter[team]: value for team, value in divisions.items()}
    playoff_info = initialize_playoff_info(standings_dict, franchise_divisions)

    atlantic_playoffs = [d for d in playoff_info if d['division'] == 'atl']
    metropolitan_playoffs = [d for d in playoff_info if d['division'] == 'met']
    central_playoffs = [d for d in playoff_info if d['division'] == 'cen']
    pacific_playoffs = [d for d in playoff_info if d['division'] == 'pac']

    divisionals = (atlantic_playoffs, metropolitan_playoffs, central_playoffs, pacific_playoffs)

    assign_seeds(divisionals)

    eastern_playoffs = sorted(atlantic_playoffs + metropolitan_playoffs, key=lambda item: (item['place'], random.random()))
    western_playoffs = sorted(central_playoffs + pacific_playoffs, key=lambda item: (item['place'], random.random()))

    determine_conference_winners(eastern_playoffs, western_playoffs)

    assign_wild_card_seeds(eastern_playoffs, 'ewc')
    assign_wild_card_seeds(western_playoffs, 'wwc')

    set_opponents(eastern_playoffs, 'atl1', 'atl2', 'ewc1', 'ewc2')
    set_opponents(eastern_playoffs, 'met1', 'met2', 'ewc1', 'ewc2')
    set_opponents(western_playoffs, 'cen1', 'cen2', 'wwc1', 'wwc2')
    set_opponents(western_playoffs, 'pac1', 'pac2', 'wwc1', 'wwc2')

    seeding_info = pd.concat([pd.DataFrame(eastern_playoffs), pd.DataFrame(western_playoffs)])
    merged_df = seeding_info.merge(standings_df).sort_values(by='points', ascending=False)

    return merged_df.reset_index(drop=True)

def simulate_a_series(team1, team2, playoff_df, verbose = False):
    converter = make_franchises_to_names()
    if verbose :
        print(f"\nstarting series between {converter[team1]} and {converter[team2]}")
    team1_games_won = 0
    team2_games_won = 0
    team1_elo = playoff_df.loc[playoff_df['franchiseId'] == team1, 'eloRating'].iloc[0]
    team2_elo = playoff_df.loc[playoff_df['franchiseId'] == team2, 'eloRating'].iloc[0]
    i = 0
    while team1_games_won != 4 and team2_games_won != 4:
        i+= 1
        team1_win_prob = win_probability(team1_elo, team2_elo)[0]
        if random.random() < team1_win_prob:
            team1_games_won += 1
            winner = team1
        else:
            team2_games_won += 1
            winner = team2

        team1_result = 1 if winner == team1 else 0

        team1_elo, team2_elo = update_elo(team1_elo, team2_elo, team1_result)

        if verbose :
            print(f"{converter[winner]} wins game {i}")
            print(f"series: {converter[team1]}: {team1_games_won}. {converter[team2]}: {team2_games_won}")

    # Update 'inPlayoffs' status of the losing team
    # Update 'inPlayoffs' status of the losing team
    if team1_games_won > team2_games_won:
        idx_team1 = playoff_df.index[playoff_df['franchiseId'] == team1][0]
        playoff_df.at[idx_team1, 'inPlayoffs'] += 1
        if verbose :
            print(f"{converter[team1]} wins {team1_games_won}-{team2_games_won}")
    else :
        idx_team2 = playoff_df.index[playoff_df['franchiseId'] == team2][0]
        playoff_df.at[idx_team2, 'inPlayoffs'] += 1
        if verbose :
            print(f"{converter[team2]} wins {team2_games_won}-{team1_games_won}")

    return playoff_df

def simulate_minibracket( minibracket: list[int], playoff_df, verbose = False) -> int :
    simulate_a_series(minibracket[0],minibracket[3],playoff_df, verbose = verbose)
    simulate_a_series(minibracket[1],minibracket[2],playoff_df, verbose = verbose)
    minibracket2 = []
    for team in minibracket: 
        if playoff_df.loc[playoff_df['franchiseId'] == team, 'inPlayoffs'].iloc[0] == 2 :
            minibracket2.append(team)

    simulate_a_series(minibracket2[0],minibracket2[1],playoff_df, verbose = verbose)
    for team in minibracket2: 
        if playoff_df.loc[playoff_df['franchiseId'] == team, 'inPlayoffs'].iloc[0] == 3 :
            winner = team

    return winner

def simiulate_final_4( minibracket: list[int], playoff_df, verbose = False) -> int :
    simulate_a_series(minibracket[0],minibracket[1],playoff_df, verbose = verbose)
    simulate_a_series(minibracket[2],minibracket[3],playoff_df, verbose = verbose)
    minibracket2 = []
    for team in minibracket: 
        if playoff_df.loc[playoff_df['franchiseId'] == team, 'inPlayoffs'].iloc[0] == 4 :
            minibracket2.append(team)
    simulate_a_series(minibracket2[0],minibracket2[1],playoff_df, verbose = verbose)
    for team in minibracket2: 
        if playoff_df.loc[playoff_df['franchiseId'] == team, 'inPlayoffs'].iloc[0] == 5 :
            winner = team

    return winner

def play_the_playoffs(simulated_season, verbose=False):
    if verbose:
        print('Simulating season...')

    converter = make_franchises_to_names()
    playoffs = make_playoff_info(simulated_season)
    playoffs = playoffs.dropna(subset=['seed'])
    playoffs = playoffs.assign(inPlayoffs=[1] * len(playoffs))

    def create_minibracket(division):
        return [
            playoffs.loc[playoffs['seed'] == f'{division}1', 'franchiseId'].iloc[0],
            playoffs.loc[playoffs['seed'] == f'{division}2', 'franchiseId'].iloc[0],
            playoffs.loc[playoffs['seed'] == f'{division}3', 'franchiseId'].iloc[0],
            playoffs.loc[playoffs['seed'] == f'{division}1', 'opponent'].iloc[0]
        ]

    divisions = ['atl', 'met', 'cen', 'pac']
    minibrackets = [create_minibracket(division) for division in divisions]

    if verbose:
        for minibracket in minibrackets:
            seeds = [playoffs.loc[playoffs['franchiseId'] == team, 'seed'].iloc[0] for team in minibracket]
            print(f"\n{seeds[0]}: {converter[minibracket[0]]}")
            print(f"{seeds[3]}: {converter[minibracket[3]]}")
            print(f"{seeds[1]}: {converter[minibracket[1]]}")
            print(f"{seeds[2]}: {converter[minibracket[2]]}")

    conf_finalists = [simulate_minibracket(bracket, playoffs, verbose=verbose) for bracket in minibrackets]
    stanley_winner = simiulate_final_4(conf_finalists, playoffs, verbose=verbose)

    if verbose:
        print(f"{converter[stanley_winner]} wins the cup")

    return playoffs

def main() :
    df = simulate_an_old_season(20182019)
    print(play_the_playoffs(df, verbose=True))

if __name__ == '__main__' :
    main()
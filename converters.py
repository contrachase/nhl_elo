import json
from pprint import pprint

def make_teams_to_franchises():
    team_file = 'all_teams.json'
    with open(team_file, 'r') as f:
        team_data = json.load(f)

    team_converter = {team['id']: team['franchiseId'] for team in team_data['data']}
    return team_converter

def make_franchises_to_names():
    franchise_file = 'all_franchises.json'
    with open(franchise_file, 'r') as f:
        franchise_data = json.load(f)

    franchise_converter = {franchise['id']: franchise['teamCommonName'] for franchise in franchise_data['data']}
    return franchise_converter
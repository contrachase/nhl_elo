import requests
import json

def main():
    response = requests.get("https://api.nhle.com/stats/rest/en/game") ###Games
    data = response.json()
    with open('all_games.json', 'w') as f:
        json.dump(data, f)
    print('Games done.')

    response = requests.get("https://api.nhle.com/stats/rest/en/franchise") ###Frachises
    data = response.json()
    with open('all_franchises.json', 'w') as f:
        json.dump(data, f)
    print('Franchises done.')

    response = requests.get("https://api.nhle.com/stats/rest/en/team") ###teams
    data = response.json()
    with open('all_teams.json', 'w') as f:
        json.dump(data, f)
    print('Teams done.')

if __name__ == '__main__':
    main()
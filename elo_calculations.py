def expected_score(player1_rating, player2_rating):
    return 1 / (1 + (10 ** ((player2_rating - player1_rating) / 400)))

def win_probability(player1_rating, player2_rating):
    expected_score_player1 = expected_score(player1_rating, player2_rating)
    expected_score_player2 = 1 - expected_score_player1
    return expected_score_player1, expected_score_player2

def update_elo(player1_rating, player2_rating, player1_result, k_factor=10 ):
    expected_score_player1 = expected_score(player1_rating, player2_rating)
    
    if player1_result == 1:
        actual_score_player1 = 1
    elif player1_result == 0.5:
        actual_score_player1 = 0.5
    else:
        actual_score_player1 = 0
    
    player1_new_rating = player1_rating + k_factor * (actual_score_player1 - expected_score_player1)
    player2_new_rating = player2_rating + k_factor * ((1 - actual_score_player1) - (1 - expected_score_player1))
    
    return int(player1_new_rating), int(player2_new_rating)
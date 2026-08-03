from similarities import score
from history import get_past_matches

def find_best_match(user, all_users):

    best_score = float('-inf')
    best_u = None

    for candidate in all_users:

        if candidate.id == user.id:

            continue

        if get_past_matches((candidate.id, user.id)) is True:

            continue

        match_score = score(user, candidate)

        if match_score > best_score:

            best_score = match_score
            best_u = candidate

    return best_u

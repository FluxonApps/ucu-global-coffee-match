def score(user1, user2):

    u1 = set(user1.interests)
    u2 = set(user2.interests)

    c = u1.intersection(u2)

    return len(c)


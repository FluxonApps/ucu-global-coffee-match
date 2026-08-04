# backend/app/matching/similarity.py

def score(user1, user2):
    return len(
        set(user1["personal_interests"] or [])
        & set(user2["personal_interests"] or [])
    )

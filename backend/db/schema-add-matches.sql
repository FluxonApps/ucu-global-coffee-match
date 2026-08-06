-- Add matches tables and slack fields
CREATE TABLE IF NOT EXISTS matches (
  id SERIAL PRIMARY KEY,
  match_type TEXT NOT NULL DEFAULT 'one_to_one',
  conversation_topics TEXT[] DEFAULT ARRAY[]::TEXT[],
  matched_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS match_participants (
  id SERIAL PRIMARY KEY,
  match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL
);

-- Add slack_user_id and is_available to users if they don't exist
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS slack_user_id TEXT,
  ADD COLUMN IF NOT EXISTS is_available BOOLEAN DEFAULT TRUE;

CREATE TABLE IF NOT EXISTS users (
  id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

  -- Registration
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  verification_code TEXT UNIQUE NOT NULL,

  -- Profile
  avatar_url TEXT DEFAULT '/static/avatars/default.png',
  role_title TEXT,
  department TEXT,
  timezone TEXT,
  bio TEXT,

  -- Interests & Skills
  personal_interests TEXT[] NOT NULL DEFAULT '{}',
  conversation_topics TEXT[] NOT NULL DEFAULT '{}',
  skills TEXT[] NOT NULL DEFAULT '{}',
  languages TEXT[] NOT NULL DEFAULT '{}',

  slack_user_id TEXT,
  is_available BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

CREATE TABLE IF NOT EXISTS matches (
  id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  match_type TEXT NOT NULL CHECK (match_type IN ('one_to_one', 'group')),
  status TEXT NOT NULL DEFAULT 'created',
  conversation_topics TEXT[] NOT NULL DEFAULT '{}',
  matched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  notified_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS match_participants (
  match_id INT NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  PRIMARY KEY (match_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_match_participants_user_id
ON match_participants(user_id);

CREATE TABLE IF NOT EXISTS user_availability (
  user_id INT REFERENCES users(id) ON DELETE CASCADE,
  day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
  hour_slot SMALLINT NOT NULL CHECK (hour_slot >= 0),
  available BOOLEAN NOT NULL DEFAULT true,
  PRIMARY KEY (user_id, day_of_week, hour_slot)
);

CREATE TABLE IF NOT EXISTS users (
  id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

  -- Registration
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,

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
  user1_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  user2_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'created',
  matched_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT chk_different_users CHECK (user1_id <> user2_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_user_pair
ON matches (LEAST(user1_id, user2_id), GREATEST(user1_id, user2_id));

CREATE TABLE IF NOT EXISTS user_availability (
  user_id INT REFERENCES users(id) ON DELETE CASCADE,
  day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
  hour_slot SMALLINT NOT NULL CHECK (hour_slot >= 0),
  available BOOLEAN NOT NULL DEFAULT true,
  PRIMARY KEY (user_id, day_of_week, hour_slot)
);

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,

  --Registration
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,

  -- Profile
  avatar_url TEXT DEFAULT '/static/avatars/default.png',
  role_title TEXT,                      -- Role / Title (напр. "Senior Product Designer")
  department TEXT,                      -- Department (drop-down)
  timezone TEXT,                        -- Timezone (drop-down)
  bio TEXT,                             -- Bio (короткий опис про себе)

  -- Interests
  personal_interests TEXT[] DEFAULT '{}', -- Personal Interests (Coffee, Hiking, Music...)
  conversation_topics TEXT[] DEFAULT '{}',-- Conversation Topics (Career Growth, Remote Work...)
  skills TEXT[] DEFAULT '{}',             -- Skills (Figma, React, Python...)
  languages TEXT[] DEFAULT '{}',          -- Languages (English, Ukrainian...)

  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,

  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS matches (
  id SERIAL PRIMARY KEY,
  user1_id INT REFERENCES users(id) ON DELETE CASCADE,
  user2_id INT REFERENCES users(id) ON DELETE CASCADE,
  status TEXT DEFAULT 'created',

  matched_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

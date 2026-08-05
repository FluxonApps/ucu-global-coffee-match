INSERT INTO users (
  verification_code,
  first_name,
  last_name,
  email,
  password_hash,
  avatar_url,
  role_title,
  department,
  timezone,
  bio,
  personal_interests,
  conversation_topics,
  skills,
  languages
) VALUES
(
  'aX9kL2mP8qR4vW1z',
  'Alex',
  'Chen',
  'alex@company.com',
  '$2b$12$AZS7YHYJ5GXicvG6/TuMxun30kRIDDJJTKQ651NrQjO/ClFSXvJQm',
  '/static/avatars/default.png',
  'Senior Product Designer',
  'Design',
  'Europe/Kyiv',
  'Passionate about UI/UX and web technologies. Always open for a coffee chat!',
  ARRAY['Coffee', 'Photography', 'Reading', 'Music'],
  ARRAY['Product Strategy', 'Design-Engineering Collaboration', 'Remote Work'],
  ARRAY['Figma', 'UX Research', 'Prototyping', 'Design Systems'],
  ARRAY['English', 'Ukrainian']
),
(
  'bY0mL3nQ9sS5wX2a',
  'Matfhei',
  'Ov',
  'matfheiwovubdjs@gmail.com',
  '$2b$12$AZS7YHYJ5GXicvG6/TuMxun30kRIDDJJTKQ651NrQjO/ClFSXvJQm',
  '/static/avatars/default.png',
  'Software Engineer',
  'Engineering',
  'Europe/Kyiv',
  'Love building backends and exploring new frameworks.',
  ARRAY['Coffee', 'Gaming', 'Open Source'],
  ARRAY['Engineering Culture', 'Cross-team Collaboration'],
  ARRAY['Python', 'FastAPI', 'PostgreSQL', 'Docker'],
  ARRAY['English', 'Ukrainian']
)
ON CONFLICT (email) DO NOTHING;
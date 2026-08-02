-- Password for all seed users is "password123".
INSERT INTO
  users (email, password_hash, name, team, timezone)
VALUES
  (
    'aboba@example.com',
    '$2b$12$AZS7YHYJ5GXicvG6/TuMxun30kRIDDJJTKQ651NrQjO/ClFSXvJQm', -- password123
    'aboba',
    'Team A',
    'Europe/Kyiv'
  ),
  (
    '67@example.com',
    '$2b$12$AZS7YHYJ5GXicvG6/TuMxun30kRIDDJJTKQ651NrQjO/ClFSXvJQm', -- password123
    'mr. 67',
    'Team B',
    'Europe/Kyiv'
  )
ON CONFLICT (email) DO NOTHING;

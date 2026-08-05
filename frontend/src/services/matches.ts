// Data-access layer for matches/colleagues/feedback.
//
// The backend does not implement matching yet, so every function here
// resolves mock data instead of calling `apiFetch`. Pages import *these*
// functions rather than `COLLEAGUES` / `MOCK_MATCHES` directly, so wiring up
// the real backend later only means editing this file.
//
// TODO(backend): once real endpoints exist, replace the bodies below with:
//   return apiFetch<Match[]>('/matches');
//   return apiFetch<Colleague>(`/colleagues/${id}`);
//   return apiFetch<void>('/feedback', { method: 'POST', body: JSON.stringify(payload) });

import { apiFetch, ApiError } from '../lib/api.ts';
import type { Colleague, Match } from '../types/coffeeMatch.ts';


export type MatchHistoryEntry = {
  id: number;
  matched_at: string;
  recommended_time: {
    utc: string;
    user_local: { timezone: string; display: string };
    match_local: { timezone: string; display: string };
    duration_minutes: number;
  } | null;
  conversation_topics: string[];
  colleague: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    avatar_url: string;
  };
};

export async function getMatchHistory(): Promise<MatchHistoryEntry[]> {
  return apiFetch<MatchHistoryEntry[]>('/matches/history');
}

export type CreateMatchResponse = {
  match: {
    id: number;
    first_name: string;
    last_name: string;
    email: string;
    timezone: string | null;
    avatar_url: string;
  };
  match_record: {
    user1_id: number;
    user2_id: number;
  };
  recommended_time: MatchHistoryEntry['recommended_time'];
  conversation_topics: string[];
};

export async function createMatch(): Promise<CreateMatchResponse> {
  return apiFetch<CreateMatchResponse>('/matches/create', { method: 'POST' });
}

export async function getMatches(): Promise<Match[]> {
  return apiFetch<Match[]>('/matches');
}

type UserProfileResponse = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  avatar_url: string;
  role_title: string | null;
  department: string | null;
  timezone: string | null;
  bio: string | null;
  personal_interests: string[];
  conversation_topics: string[];
  skills: string[];
  languages: string[];
};

const toColleague = (row: UserProfileResponse): Colleague => ({
  id: String(row.id),
  name: `${row.first_name} ${row.last_name}`.trim(),
  role: row.role_title ?? '',
  department: row.department ?? '',
  location: '',
  timezone: row.timezone ?? '',
  bio: row.bio ?? '',
  avatar: row.avatar_url,
  skills: row.skills,
  interests: row.personal_interests,
  languages: row.languages,
  availability: [],
  format: [],
  duration: '',
  frequency: '',
});

export async function getAllColleagues(): Promise<Colleague[]> {
  const rows = await apiFetch<UserProfileResponse[]>('/users');
  return rows.map(toColleague);
}

export async function getColleague(id: string): Promise<Colleague | undefined> {
  try {
    const row = await apiFetch<UserProfileResponse>(`/users/${id}`);
    return toColleague(row);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return undefined;
    }
    throw error;
  }
}

export interface FeedbackAnswers {
  matchId: string;
  ratings: Record<string, number>;
  comment: string;
}

export async function submitFeedback(answers: FeedbackAnswers): Promise<void> {
  // TODO(backend): POST /feedback
  console.info('[mock] feedback submitted (not persisted):', answers);
}

/** The one match still awaiting feedback, used by the Feedback page. */
export async function getMatchNeedingFeedback(): Promise<Match | undefined> {
  const matches = await getMatches();
  return matches.find((m) => m.status === 'previous' && !m.feedbackGiven);
}

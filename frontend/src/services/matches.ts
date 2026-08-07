import { apiFetch, ApiError } from '../lib/api.ts';
import type { Colleague, Match } from '../types/coffeeMatch.ts';

export type MatchParticipant = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  timezone: string | null;
  avatar_url: string;
};

// Returned for one_to_one matches (get_recommended_time_between_users).
export type OneToOneRecommendedTime = {
  utc: string;
  utc_iso?: string;
  user_local: {
    timezone: string;
    display: string;
  };
  match_local: {
    timezone: string;
    display: string;
  };
  duration_minutes: number;
};

// Returned for group matches (get_recommended_time_for_group).
export type GroupRecommendedTime = {
  utc: string;
  utc_iso?: string;
  participants: {
    user_id: number;
    timezone: string;
    display: string;
  }[];
  duration_minutes: number;
};

export type RecommendedTime = OneToOneRecommendedTime | GroupRecommendedTime;

export type MatchHistoryEntry = {
  id: number;
  matched_at: string;

  match_type: 'one_to_one' | 'group';

  recommended_time: RecommendedTime | null;

  conversation_topics: string[];

  participants: MatchParticipant[];
};

export async function getMatchHistory(): Promise<MatchHistoryEntry[]> {
  return apiFetch<MatchHistoryEntry[]>('/matches/history');
}

export type CreateMatchResponse = {
  id: number;

  match_type: 'one_to_one' | 'group';

  participants: MatchParticipant[];

  recommended_time: RecommendedTime | null;

  conversation_topics: string[];
};

export async function createMatch(matchType: 'one_to_one' | 'group'): Promise<CreateMatchResponse> {
  return apiFetch<CreateMatchResponse>('/matches/create', {
    method: 'POST',
    body: JSON.stringify({
      match_type: matchType,
    }),
  });
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

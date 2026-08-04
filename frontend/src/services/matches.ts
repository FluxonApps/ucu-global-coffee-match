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

import { COLLEAGUES, MOCK_MATCHES } from '../data/mockMatches.ts';
import { apiFetch } from '../lib/api.ts';
import type { Colleague, Match } from '../types/coffeeMatch.ts';
import { apiFetch } from '../lib/api.ts';

export type MatchHistoryEntry = {
  id: number;
  matched_at: string;
  colleague: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
  };
};

export async function getMatchHistory(): Promise<MatchHistoryEntry[]> {
  return apiFetch<MatchHistoryEntry[]>('/matches/history');
}

export async function getMatches(): Promise<Match[]> {
  return apiFetch<Match[]>('/matches');
}

export async function getColleague(id: string): Promise<Colleague | undefined> {
  // TODO(backend): GET /colleagues/:id
  return COLLEAGUES.find((c) => c.id === id);
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

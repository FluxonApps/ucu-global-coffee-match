// Domain types for the Coffee Match product.
//
// These mirror what the Figma mock used. `Colleague` and `Match` don't have a
// backend yet — see `src/services/matches.ts`. Once the backend adds
// matching, colleagues, and profile-detail endpoints, these types should be
// reconciled with the real Pydantic response schemas.

export interface ProfileDetails {
  role: string;
  department: string;
  timezone: string;
  bio: string;
  photoUrl: string;
  skills: string[];
  interests: string[];
  languages: string[];
  topics: string[];
  /** Slot format: "Mon-09", "Tue-14", etc. */
  availability: string[];
  format: string[];
  duration: string;
  frequency: string;
  slackConnected: boolean;
  slackHandle: string;
}

export interface Colleague {
  id: string;
  name: string;
  role: string;
  department: string;
  location: string;
  timezone: string;
  bio: string;
  avatar: string;
  skills: string[];
  interests: string[];
  languages: string[];
  topics: string[];
  availability: string[];
  format: string[];
  duration: string;
  frequency: string;
}

export type MatchStatus = 'current' | 'upcoming' | 'previous';

export interface Match {
  id: string;
  colleague: Colleague;
  status: MatchStatus;
  matchDate: string;
  scheduledDate?: string;
  sharedInterests: string[];
  feedbackGiven?: boolean;
}

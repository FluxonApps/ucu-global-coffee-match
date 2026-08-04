// Holds the profile fields the backend doesn't persist yet: bio, skills,
// interests, topics, languages, availability, format/duration/frequency
// preferences, and the Slack handle. `name`/`team`/`timezone` live on the
// real `User` from `AuthContext` instead — see `useAuth()`.
//
// TODO(backend): once `/users/me` accepts these fields (or a dedicated
// profile-details endpoint exists), replace the localStorage read/write
// below with `apiFetch` calls and delete this file's persistence bits.

import { createContext, useEffect, useState } from 'react';
import type { PropsWithChildren } from 'react';

import { useAuth } from './useAuth.ts';
import type { ProfileDetails } from '../types/coffeeMatch.ts';

const EMPTY_DETAILS: ProfileDetails = {
  role: '',
  department: '',
  timezone: '',
  bio: '',
  photoUrl: '',
  skills: [],
  interests: [],
  languages: [],
  topics: [],
  availability: [],
  format: [],
  duration: '30 minutes',
  frequency: 'Twice a month',
  slackConnected: false,
  slackHandle: '',
};

function storageKey(userId: number) {
  return `coffee-match:profile-details:${userId}`;
}

export type ProfileDetailsContextValue = {
  details: ProfileDetails;
  setDetails: (fields: Partial<ProfileDetails>) => void;
};

export const ProfileDetailsContext = createContext<ProfileDetailsContextValue | null>(null);

export const ProfileDetailsProvider = ({ children }: PropsWithChildren) => {
  const { user } = useAuth();
  const [details, setDetailsState] = useState<ProfileDetails>(EMPTY_DETAILS);

  useEffect(() => {
    if (!user) {
      setDetailsState(EMPTY_DETAILS);
      return;
    }
    try {
      const raw = localStorage.getItem(storageKey(user.id));
      setDetailsState(raw ? { ...EMPTY_DETAILS, ...JSON.parse(raw) } : EMPTY_DETAILS);
    } catch {
      setDetailsState(EMPTY_DETAILS);
    }
  }, [user]);

  const setDetails = (fields: Partial<ProfileDetails>) => {
    setDetailsState((prev) => {
      const next = { ...prev, ...fields };
      if (user) {
        try {
          localStorage.setItem(storageKey(user.id), JSON.stringify(next));
        } catch {
          // ignore storage failures (e.g. private browsing)
        }
      }
      return next;
    });
  };

  return <ProfileDetailsContext value={{ details, setDetails }}>{children}</ProfileDetailsContext>;
};

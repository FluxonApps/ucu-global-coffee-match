import { createContext, useState } from 'react';
import type { ReactNode } from 'react';

import type { ProfileDetails } from '../types/coffeeMatch.ts';

export interface ProfileDetailsContextValue {
  details: ProfileDetails;
  setDetails: (details: ProfileDetails) => void;
}

export const ProfileDetailsContext = createContext<ProfileDetailsContextValue | null>(null);

const DEFAULT_DETAILS: ProfileDetails = {
  role: '',
  department: '',
  timezone: '',
  bio: '',
  photoUrl: '',
  skills: [],
  interests: [],
  languages: [],
  availability: [],
  format: [],
  duration: '',
  frequency: '',
  slackConnected: false,
  slackHandle: '',
};

export const ProfileDetailsProvider = ({ children }: { children: ReactNode }) => {
  const [details, setDetails] = useState<ProfileDetails>(DEFAULT_DETAILS);

  return <ProfileDetailsContext.Provider value={{ details, setDetails }}>{children}</ProfileDetailsContext.Provider>;
};

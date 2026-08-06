import { createContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';

import type { ProfileDetails } from '../types/coffeeMatch.ts';
import { apiFetch } from '../lib/api.ts';
import { DAYS } from '../data/options.ts';
import { useAuth } from './AuthContext.tsx';

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
  const { user } = useAuth();

  useEffect(() => {
    if (!user) {
      setDetails(DEFAULT_DETAILS);
      return;
    }

    const loadProfile = async () => {
      try {
        const profile = await apiFetch<{
          role_title?: string;
          department?: string;
          timezone?: string;
          bio?: string;
          avatar_url?: string;
          skills?: string[];
          personal_interests?: string[];
          languages?: string[];
        }>('/users/me');

        const availabilityRows = await apiFetch<
          { day_of_week: number; hour_slot: number; available: boolean }[]
        >('/users/me/availability').catch((fetchError) => {
          console.error('Failed to load availability:', fetchError);
          return [];
        });

        const availability = availabilityRows
          .filter((row) => row.available)
          .flatMap((row) => {
            const day = DAYS[row.day_of_week]?.key;
            if (!day) return [];
            const hour = String(row.hour_slot).padStart(2, '0');
            return [`${day}-${hour}`];
          });

        setDetails({
          role: profile.role_title ?? '',
          department: profile.department ?? '',
          timezone: profile.timezone ?? '',
          bio: profile.bio ?? '',
          photoUrl: profile.avatar_url ?? '',
          skills: profile.skills ?? [],
          interests: profile.personal_interests ?? [],
          languages: profile.languages ?? [],
          availability,
          format: [],
          duration: '',
          frequency: '',
          slackConnected: false,
          slackHandle: '',
        });
      } catch (error) {
        console.error('Failed to load profile details:', error);
      }
    };

    loadProfile();
  }, [user?.id]);

  return (
    <ProfileDetailsContext.Provider value={{ details, setDetails }}>
      {children}
    </ProfileDetailsContext.Provider>
  );
};

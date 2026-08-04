import { use } from 'react';

import { ProfileDetailsContext } from './ProfileDetailsContext.tsx';

export const useProfileDetails = () => {
  const ctx = use(ProfileDetailsContext);
  if (!ctx) throw new Error('useProfileDetails must be used within ProfileDetailsProvider');
  return ctx;
};

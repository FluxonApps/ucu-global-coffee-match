import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

if (!import.meta.env.VITE_FIREBASE_API_KEY) {
  throw new Error('.env file not populated. Please specify Firebase config in .env');
}

// Initialize Firebase
const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);

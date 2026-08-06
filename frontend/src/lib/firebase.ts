import { initializeApp } from "firebase/app";
import { getStorage } from "firebase/storage";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: "ucu-global-coffee-match.firebaseapp.com",
  projectId: "ucu-global-coffee-match",
  storageBucket: "ucu-global-coffee-match.firebasestorage.app",
  messagingSenderId: "817312451477",
  appId: "1:817312451477:web:574e821d2c8267ccaf849c",
};

const app = initializeApp(firebaseConfig);

export const storage = getStorage(app);

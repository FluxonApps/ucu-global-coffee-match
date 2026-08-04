import { initializeApp } from "firebase/app";
import { getStorage } from "firebase/storage";

const firebaseConfig = {
  apiKey: "AIzaSyD-4z2hEzpkH0WfpLPlog6NBqSuAu_ePwA",
  authDomain: "ucu-global-coffee-match.firebaseapp.com",
  projectId: "ucu-global-coffee-match",
  storageBucket: "ucu-global-coffee-match.firebasestorage.app",
  messagingSenderId: "817312451477",
  appId: "1:817312451477:web:574e821d2c8267ccaf849c",
};

const app = initializeApp(firebaseConfig);

export const storage = getStorage(app);

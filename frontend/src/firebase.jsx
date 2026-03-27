// src/firebase.jsx
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup  } from "firebase/auth";
import { getAnalytics } from "firebase/analytics";

const firebaseConfig = {
  apiKey: "AIzaSyBMSrNU134nZek8-3lnPij_nX7wtaHSniw",
  authDomain: "finwise-d6812.firebaseapp.com",
  projectId: "finwise-d6812",
  storageBucket: "finwise-d6812.appspot.com",
  messagingSenderId: "734778749701",
  appId: "1:734778749701:web:d558818ab9a160f5143d6c",
  measurementId: "G-EPT4TET5DF"
};

const app = initializeApp(firebaseConfig);

let analytics = null;
try {
  analytics = getAnalytics(app);
} catch (e) {
  // ok in dev if analytics can't initialize
  // console.warn("Analytics not initialized:", e.message);
}

const auth = getAuth(app);
const provider = new GoogleAuthProvider();
export async function signInWithGooglePopup() {
  const result = await signInWithPopup(auth, provider);
  const idToken = await result.user.getIdToken();
  return idToken;
}
export { auth, provider, analytics };

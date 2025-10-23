// src/UserContext.jsx
import React, { createContext, useState, useEffect } from "react";
import { toast } from "react-toastify";

export const UserContext = createContext({
  user: null,
  setUser: () => {}
});

export const UserProvider = ({ children }) => {
  const [user, setUserState] = useState(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("user");
      if (raw) setUserState(JSON.parse(raw));
    } catch (e) {
      console.error("UserProvider load error:", e);
    }
  }, []);

  // persist + show greeting toast when user logs in
  const setUser = (u) => {
    try {
      if (u) {
        localStorage.setItem("user", JSON.stringify(u));
        // friendly toast
        const name = u.name || u.phone || "User";
        toast.info(`Hi, ${name}`, { autoClose: 2500 });
      } else {
        localStorage.removeItem("user");
      }
    } catch (e) { /* ignore */ }
    setUserState(u);
  };

  return (
    <UserContext.Provider value={{ user, setUser }}>
      {children}
    </UserContext.Provider>
  );
};

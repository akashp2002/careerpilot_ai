import { createContext, useContext, useState, type ReactNode } from "react";

const STORAGE_KEY = "careerpilot_session_id";

interface SessionContextValue {
  sessionId: string | null;
  setSessionId: (id: string | null) => void;
}

const SessionContext = createContext<SessionContextValue | undefined>(undefined);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [sessionId, setSessionIdState] = useState<string | null>(() =>
    sessionStorage.getItem(STORAGE_KEY)
  );

  const setSessionId = (id: string | null) => {
    setSessionIdState(id);
    if (id) {
      sessionStorage.setItem(STORAGE_KEY, id);
    } else {
      sessionStorage.removeItem(STORAGE_KEY);
    }
  };

  return (
    <SessionContext.Provider value={{ sessionId, setSessionId }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}
/**
 * useSession — session UUID management
 * Stores session_id in sessionStorage (clears on tab close).
 */

import { useState, useCallback } from 'react';

const KEY = 'resumeiq_session_id';

export function useSession() {
  const [sessionId, setSessionIdState] = useState(
    () => sessionStorage.getItem(KEY)
  );

  const setSessionId = useCallback((id) => {
    sessionStorage.setItem(KEY, id);
    setSessionIdState(id);
  }, []);

  const clearSession = useCallback(() => {
    sessionStorage.removeItem(KEY);
    setSessionIdState(null);
  }, []);

  return { sessionId, setSessionId, clearSession };
}

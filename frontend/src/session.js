export function clearFrontendSession(setSession, setActiveView, setState) {
  setSession(null);
  setActiveView("dashboard");
  setState((current) => ({
    ...current,
    patients: [], psychologists: [], appointments: [], records: [], payments: [], expenses: [],
    loading: false
  }));
}

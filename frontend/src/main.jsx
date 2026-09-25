import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  BadgeDollarSign,
  CalendarDays,
  ChartNoAxesColumnIncreasing,
  CheckCircle2,
  ClipboardList,
  Cog,
  Home,
  Lock,
  LogOut,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Stethoscope,
  UserRound,
  UsersRound
} from "lucide-react";
import "./styles.css";
import { ApiError, apiRequest, authenticate, buildAppointmentPatch, buildFinancePeriodQuery, buildSettingsPayload, canAccessFinancialUi, canAccessUserManagement, formatCompetencePeriod, formatMoneyFromCents, nextCompetencePeriod, parseCompetencePeriod, parseMoneyToCents } from "./api.js";
import { clearFrontendSession } from "./session.js";

const today = new Date().toISOString().slice(0, 10);
const defaultPeriodStart = `${today.slice(0, 7)}-01`;
const defaultPeriodEnd = (() => {
  const value = new Date(`${defaultPeriodStart}T00:00:00Z`);
  value.setUTCMonth(value.getUTCMonth() + 1);
  return value.toISOString().slice(0, 10);
})();
const defaultCompetencePeriod = today.slice(0, 7);
const defaultCompetenceEnd = nextCompetencePeriod(defaultCompetencePeriod);

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: Home },
  { id: "patients", label: "Pacientes", icon: UsersRound },
  { id: "psychologists", label: "Psicologos", icon: Stethoscope },
  { id: "agenda", label: "Agenda", icon: CalendarDays },
  { id: "records", label: "Prontuario", icon: ClipboardList },
  { id: "finance", label: "Financeiro", icon: BadgeDollarSign },
  { id: "reports", label: "Relatorios", icon: ChartNoAxesColumnIncreasing },
  { id: "settings", label: "Configuracoes", icon: Cog }
  ,{ id: "users", label: "Usuarios", icon: UsersRound }
];

const statusLabels = {
  scheduled: "Agendado",
  canceled: "Cancelado",
  done: "Realizado",
  no_show: "Falta",
  pending: "Pendente",
  paid: "Pago",
  active: "Ativa",
  reversed: "Estornado"
};

const money = formatMoneyFromCents;

function App() {
  const [session, setSession] = useState(null);
  const [activeView, setActiveView] = useState("dashboard");
  const [state, setState] = useState({
    dashboard: null,
    patients: [],
    psychologists: [],
    appointments: [],
    records: [],
    payments: [],
    expenses: [],
    categories: [],
    settings: null,
    users: [],
    finance: null,
    financeError: "",
    error: "",
    license: null,
    online: false,
    loading: true
  });

  const logout = () => {
    clearFrontendSession(setSession, setActiveView, setState);
  };

  const loadData = async (currentSession = session) => {
    if (!currentSession) return;
    setState((current) => ({ ...current, loading: true }));
    try {
      const token = currentSession.token;
      const recordsRequest = currentSession.user.role === "psychologist"
        ? apiRequest("/clinical-records", { token })
        : Promise.resolve([]);
      const financeAllowed = canAccessFinancialUi(currentSession.user.role);
      const financeQuery = `start=${defaultPeriodStart}&end=${defaultPeriodEnd}&regime=cash`;
      const settingsRequest = currentSession.user.role === "admin" ? apiRequest("/settings", { token }) : Promise.resolve(null);
      const usersRequest = canAccessUserManagement(currentSession.user.role) ? apiRequest("/users", { token }) : Promise.resolve([]);
      const [health, license, dashboard, patients, psychologists, appointments, records, payments, expenses, finance, categories, settings, users] =
      await Promise.all([
        apiRequest("/health"),
        apiRequest("/license/status"),
        apiRequest("/dashboard/summary", { token }),
        apiRequest("/patients", { token }),
        apiRequest("/psychologists", { token }),
        apiRequest("/appointments", { token }),
        recordsRequest,
        financeAllowed ? apiRequest(`/finance/payments?${financeQuery}`, { token }) : Promise.resolve([]),
        financeAllowed ? apiRequest(`/finance/expenses?${financeQuery}`, { token }) : Promise.resolve([]),
        financeAllowed ? apiRequest(`/finance/summary?${financeQuery}`, { token }) : Promise.resolve(null),
        financeAllowed ? apiRequest("/finance/categories", { token }) : Promise.resolve([]),
        settingsRequest, usersRequest
      ]);
      setState({ license, dashboard, patients, psychologists, appointments, records, payments, expenses, finance, categories, settings, users, financeError: "", error: "", online: Boolean(health), loading: false });
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) logout();
      setState((current) => ({
        ...current,
        dashboard: null, patients: [], psychologists: [], appointments: [], records: [],
        payments: [], expenses: [], categories: [], settings: null, users: [], finance: null,
        financeError: error instanceof ApiError ? error.message : "Nao foi possivel carregar o financeiro.",
        error: "Nao foi possivel carregar os dados operacionais. Verifique a API e tente novamente.",
        online: false, loading: false
      }));
    }
  };

  const loadFinance = async (period) => {
    const query = buildFinancePeriodQuery(period);
    setState((current) => ({ ...current, loading: true, financeError: "" }));
    try {
      const [payments, expenses, finance] = await Promise.all([
        apiRequest(`/finance/payments?${query}`, { token: session.token }),
        apiRequest(`/finance/expenses?${query}`, { token: session.token }),
        apiRequest(`/finance/summary?${query}`, { token: session.token })
      ]);
      setState((current) => ({ ...current, payments, expenses, finance, loading: false, financeError: "" }));
    } catch (error) {
      setState((current) => ({
        ...current,
        payments: [], expenses: [], finance: {
          regime: period.regime,
          start: period.regime === "cash" ? period.cashStart : period.accrualStart,
          end: period.regime === "cash" ? period.cashEnd : period.accrualEnd
        },
        loading: false,
        financeError: error instanceof ApiError ? error.message : "Nao foi possivel carregar o periodo financeiro."
      }));
    }
  };

  const submit = async (path, payload, method = "POST", headers = {}) => {
    try {
      const result = await apiRequest(path, { method, body: JSON.stringify(payload), token: session.token, headers });
      await loadData();
      return result;
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) logout();
      throw error;
    }
  };

  useEffect(() => {
    Promise.all([apiRequest("/health"), apiRequest("/license/status")])
      .then(([health, license]) => setState((current) => ({ ...current, online: Boolean(health), license, loading: false })))
      .catch(() => setState((current) => ({ ...current, online: false, license: null, loading: false })));
  }, []);

  useEffect(() => {
    if (session) loadData(session);
  }, [session]);

  if (!session) {
    return <LoginScreen onLogin={setSession} online={state.online} license={state.license} />;
  }

  return (
    <div className="appShell">
      <Sidebar activeView={activeView} setActiveView={setActiveView} user={session.user} onLogout={logout} />
      <main className="workspace">
        <Topbar online={state.online} loading={state.loading} onRefresh={loadData} activeView={activeView} license={state.license} />
        <ViewRouter activeView={activeView} data={state} submit={submit} reload={loadData} loadFinance={loadFinance} user={session.user} />
      </main>
    </div>
  );
}

function LoginScreen({ onLogin, online, license }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    if (license && !license.valid) {
      setError(license.message || "Licenca expirada ou invalida.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      onLogin(await authenticate(username, password));
      setPassword("");
    } catch (requestError) {
      setError(requestError instanceof ApiError && requestError.status === 401
        ? "Usuario ou senha invalidos."
        : "Nao foi possivel conectar a API. Verifique se o servidor esta ativo.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="loginPage">
      <section className="loginPanel">
        <div className="brandMark">
          <span className="brandMonogram">MG</span>
        </div>
        <h1>Marilia Gabriela Gaspar</h1>
        <p className="muted">Psicologa - CRP 11/20433 | Desenvolvimento Infantil</p>
        <form onSubmit={submit} className="loginForm">
          <label>
            Usuario
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoFocus />
          </label>
          <label>
            Senha
            <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" />
          </label>
          {error ? <div className="formError">{error}</div> : null}
          <button className="primaryButton" disabled={loading}>
            <Lock size={18} />
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>
        <div className={online ? "statusPill online" : "statusPill offline"}>
          <Activity size={16} />
          {online ? "API conectada" : "API indisponivel"}
        </div>
        <LicenseNotice license={license} />
      </section>
    </div>
  );
}

function LicenseNotice({ license }) {
  if (!license) {
    return null;
  }
  const label = license.type === "full" ? "Licenca completa" : "Teste gratuito";
  return (
    <div className={license.valid ? "licenseNotice valid" : "licenseNotice invalid"}>
      <strong>{label}</strong>
      <span>{license.message}</span>
      {license.expires_at ? <span>Validade: {license.expires_at}</span> : null}
      {license.valid ? <span>Dias restantes: {license.days_left}</span> : null}
    </div>
  );
}

function Sidebar({ activeView, setActiveView, user, onLogout }) {
  const visibleNavItems = navItems.filter((item) => {
    if (item.id === "records") return user.role === "psychologist";
    if (item.id === "settings") return user.role === "admin";
    if (item.id === "users") return canAccessUserManagement(user.role);
    if (item.id === "finance" || item.id === "reports") return canAccessFinancialUi(user.role);
    return true;
  });
  return (
    <aside className="sidebar">
      <div className="sidebarBrand">
        <div className="brandIcon">
          <span className="brandMonogram small">MG</span>
        </div>
        <div>
          <strong>Marilia Gaspar</strong>
          <span>Psicologia infantil</span>
        </div>
      </div>
      <nav className="navList">
        {visibleNavItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              className={activeView === item.id ? "navButton active" : "navButton"}
              onClick={() => setActiveView(item.id)}
              title={item.label}
            >
              <Icon size={19} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
      <div className="userBox">
        <UserRound size={20} />
        <div>
          <strong>{user.name}</strong>
          <span>{user.role}</span>
        </div>
        <button className="iconButton" onClick={onLogout} title="Sair">
          <LogOut size={18} />
        </button>
      </div>
    </aside>
  );
}

function Topbar({ online, loading, onRefresh, activeView, license }) {
  const title = navItems.find((item) => item.id === activeView)?.label || "Dashboard";
  return (
    <header className="topbar">
      <div>
        <h2>{title}</h2>
        <span>Agenda, acolhimento, prontuario e financeiro em uma rotina leve.</span>
      </div>
      <div className="topbarActions">
        <span className={online ? "statusPill online" : "statusPill offline"}>
          <Activity size={16} />
          {online ? "API online" : "API indisponivel"}
        </span>
        <span className={license?.valid ? "statusPill online" : "statusPill offline"}>
          {license?.valid ? `Licenca: ${license.days_left} dias` : "Licenca bloqueada"}
        </span>
        <button className="iconTextButton" onClick={onRefresh} disabled={loading}>
          <RefreshCw size={17} />
          Atualizar
        </button>
      </div>
    </header>
  );
}

function ViewRouter({ activeView, data, submit, reload, loadFinance, user }) {
  if (data.loading && !data.dashboard) return <LoadingState />;
  if (data.error) return <ErrorState text={data.error} onRetry={reload} />;
  const map = {
    dashboard: <Dashboard data={data} />,
    patients: <Patients data={data} reload={reload} />,
    psychologists: <Psychologists data={data} />,
    agenda: <Agenda data={data} submit={submit} user={user} />,
    records: <ClinicalRecords data={data} submit={submit} />,
    finance: user.role === "psychologist" ? <EmptyState text="Modulo financeiro indisponivel para este perfil." /> : <Finance data={data} submit={submit} loadFinance={loadFinance} user={user} />,
    reports: <Reports data={data} />,
    settings: <Settings data={data.settings} submit={submit} />,
    users: user.role === "admin" ? <Users data={data.users} submit={submit} reload={reload} currentUser={user} /> : <EmptyState text="Modulo de usuarios indisponivel para este perfil." />
  };
  return <section className="view">{map[activeView]}</section>;
}

function Dashboard({ data }) {
  const done = data.appointments.filter((item) => item.status === "done").length;
  const canceled = data.appointments.filter((item) => item.status === "canceled").length;
  const scheduled = data.appointments.filter((item) => item.status === "scheduled").length;
  return (
    <>
      <div className="metricGrid">
        <Metric title="Pacientes ativos" value={data.dashboard.active_patients} icon={UsersRound} />
        <Metric title="Agenda hoje" value={data.dashboard.appointments_today} icon={CalendarDays} />
        <Metric title="Recebido no caixa do mes" value={money(data.dashboard.received_cents)} icon={BadgeDollarSign} />
        <Metric title="Saldo de caixa do mes" value={money(data.dashboard.balance_cents)} icon={ChartNoAxesColumnIncreasing} />
      </div>
      <div className="contentGrid">
        <Panel title="Proximos atendimentos">
          <AppointmentList appointments={data.appointments.slice(0, 6)} patients={data.patients} psychologists={data.psychologists} />
        </Panel>
        <Panel title="Situacao operacional">
          <div className="statusBoard">
            <InfoRow label="Agendados" value={scheduled} />
            <InfoRow label="Realizados" value={done} />
            <InfoRow label="Cancelados" value={canceled} />
            <InfoRow label="Despesas de caixa" value={money(data.dashboard.expense_cents)} />
            <InfoRow label="Recebido em caixa" value={money(data.dashboard.received_cents)} strong />
          </div>
        </Panel>
      </div>
    </>
  );
}

function Patients({ data, reload }) {
  const [search, setSearch] = useState("");
  const filtered = data.patients.filter((patient) => patient.full_name.toLowerCase().includes(search.toLowerCase()));

  return (
    <Panel
      title="Pacientes"
      action={
        <button className="iconTextButton" onClick={reload}>
          <RefreshCw size={17} />
          Recarregar
        </button>
      }
    >
      <ToolbarSearch value={search} onChange={setSearch} placeholder="Buscar paciente" />
      <DataTable
        columns={["Nome", "CPF", "Telefone", "E-mail", "Status"]}
        rows={filtered.map((patient) => [
          patient.full_name,
          patient.cpf,
          patient.phone,
          patient.email,
          patient.active ? "Ativo" : "Inativo"
        ])}
      />
    </Panel>
  );
}

function Psychologists({ data }) {
  return (
    <Panel title="Psicologos">
      <DataTable
        columns={["Nome", "CRP", "Especialidade", "Telefone", "Status"]}
        rows={data.psychologists.map((psychologist) => [
          psychologist.full_name,
          psychologist.crp,
          psychologist.specialty,
          psychologist.phone,
          psychologist.active ? "Ativo" : "Inativo"
        ])}
      />
    </Panel>
  );
}

function Agenda({ data, submit, user }) {
  const [filters, setFilters] = useState({ targetDate: today, psychologistId: "", view: "day" });
  const [editingAppointment, setEditingAppointment] = useState(null);
  const [editForm, setEditForm] = useState(null);
  const [editError, setEditError] = useState("");
  const [form, setForm] = useState({
    patient_id: data.patients[0]?.id || "",
    psychologist_id: data.psychologists[0]?.id || "",
    scheduled_date: today,
    scheduled_time: "09:00",
    duration_minutes: 50,
    notes: ""
  });
  const patientById = Object.fromEntries(data.patients.map((patient) => [patient.id, patient]));
  const psychologistById = Object.fromEntries(data.psychologists.map((psychologist) => [psychologist.id, psychologist]));
  const range = useMemo(() => {
    const start = new Date(`${filters.targetDate}T00:00:00`);
    const end = new Date(start);
    if (filters.view === "week") end.setDate(end.getDate() + 7);
    else if (filters.view === "list") end.setDate(end.getDate() + 31);
    else end.setDate(end.getDate() + 1);
    return { start, end };
  }, [filters.targetDate, filters.view]);
  const filtered = data.appointments.filter((appointment) => {
    const appointmentDate = new Date(appointment.scheduled_at);
    const sameDate = appointmentDate >= range.start && appointmentDate < range.end;
    const samePsychologist = !filters.psychologistId || Number(filters.psychologistId) === appointment.psychologist_id;
    return sameDate && samePsychologist;
  });

  const createAppointment = async (event) => {
    event.preventDefault();
    await submit("/appointments", {
      patient_id: Number(form.patient_id),
      psychologist_id: Number(form.psychologist_id),
      scheduled_at: `${form.scheduled_date}T${form.scheduled_time}:00`,
      duration_minutes: Number(form.duration_minutes),
      status: "scheduled",
      notes: form.notes
    });
  };

  const changeStatus = async (appointment, status) => {
    const action = status === "no_show" ? "no-show" : status;
    await submit(`/appointments/${appointment.id}/${action}`, { reason: "" }, "POST", { "If-Match": `"${appointment.version}"` });
  };

  const reschedule = async (appointment) => {
    const scheduledAt = window.prompt("Nova data e hora (AAAA-MM-DDTHH:MM)", appointment.scheduled_at.slice(0, 16));
    const reason = scheduledAt && window.prompt("Motivo operacional da remarcacao");
    if (!scheduledAt || !reason) return;
    await submit(`/appointments/${appointment.id}/reschedule`, {
      patient_id: appointment.patient_id, psychologist_id: appointment.psychologist_id,
      scheduled_at: `${scheduledAt}:00`, duration_minutes: appointment.duration_minutes,
      notes: appointment.notes, timezone_name: appointment.timezone_name || "America/Sao_Paulo", reason
    }, "POST", { "If-Match": `"${appointment.version}"` });
  };

  const startEdit = (appointment) => {
    setEditingAppointment(appointment);
    setEditError("");
    setEditForm({
      scheduled_date: appointment.scheduled_at.slice(0, 10),
      scheduled_time: appointment.scheduled_at.slice(11, 16),
      duration_minutes: String(appointment.duration_minutes),
      notes: appointment.notes || ""
    });
  };

  const cancelEdit = () => {
    setEditingAppointment(null);
    setEditForm(null);
    setEditError("");
  };

  const saveEdit = async (event) => {
    event.preventDefault();
    const changes = buildAppointmentPatch(editingAppointment, editForm);
    if (!Object.keys(changes).length) return;

    setEditError("");
    try {
      await submit(`/appointments/${editingAppointment.id}`, changes, "PATCH", {
        "If-Match": `"${editingAppointment.version}"`
      });
      cancelEdit();
    } catch (error) {
      setEditError(error instanceof ApiError ? error.message : "Nao foi possivel editar o atendimento.");
    }
  };

  return (
    <div className="splitGrid">
      <Panel title="Agenda de atendimentos">
        <div className="agendaHeader">
          <input
            type="date"
            value={filters.targetDate}
            onChange={(event) => setFilters({ ...filters, targetDate: event.target.value })}
          />
          <select
            value={filters.psychologistId}
            onChange={(event) => setFilters({ ...filters, psychologistId: event.target.value })}
          >
            <option value="">Todos os psicologos</option>
            {data.psychologists.map((psychologist) => (
              <option key={psychologist.id} value={psychologist.id}>
                {psychologist.full_name}
              </option>
            ))}
          </select>
          <div className="viewTabs" role="tablist" aria-label="Visualizacao da agenda">
            {[['list', 'Lista'], ['day', 'Dia'], ['week', 'Semana']].map(([value, label]) => (
              <button key={value} type="button" role="tab" aria-selected={filters.view === value}
                className={filters.view === value ? "tabButton active" : "tabButton"}
                onClick={() => setFilters({ ...filters, view: value })}>{label}</button>
            ))}
          </div>
        </div>
        <div className="appointmentList">
          {filtered.map((appointment) => (
            <div className="appointmentItem actionItem" key={appointment.id}>
              <div className="timeBlock">{new Date(appointment.scheduled_at).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</div>
              <div>
                <strong>{patientById[appointment.patient_id]?.full_name || "Paciente"}</strong>
                <span>{psychologistById[appointment.psychologist_id]?.full_name || "Psicologo"} - {appointment.duration_minutes} min</span>
                <small>{appointment.notes || "Sem observacoes"}</small>
              </div>
              <div className="rowActions">
                <span className={`statusTag ${appointment.status}`}>{statusLabels[appointment.status] || appointment.status}</span>
                {appointment.status === "scheduled" ? <button onClick={() => startEdit(appointment)} title="Editar atendimento"><Pencil size={16} /> Editar</button> : null}
                {appointment.status === "scheduled" && user.role !== "reception" ? <button onClick={() => changeStatus(appointment, "done")}>Realizar</button> : null}
                {appointment.status === "scheduled" ? <button onClick={() => changeStatus(appointment, "no_show")}>Falta</button> : null}
                {appointment.status === "scheduled" ? <button onClick={() => reschedule(appointment)}>Remarcar</button> : null}
                {appointment.status === "scheduled" ? <button onClick={() => changeStatus(appointment, "canceled")}>Cancelar</button> : null}
              </div>
              {editingAppointment?.id === appointment.id && editForm ? (
                <form className="inlineFields" onSubmit={saveEdit}>
                  <label>Data<input type="date" value={editForm.scheduled_date} onChange={(event) => setEditForm({ ...editForm, scheduled_date: event.target.value })} /></label>
                  <label>Hora<input type="time" value={editForm.scheduled_time} onChange={(event) => setEditForm({ ...editForm, scheduled_time: event.target.value })} /></label>
                  <label>Duracao<input value={editForm.duration_minutes} onChange={(event) => setEditForm({ ...editForm, duration_minutes: event.target.value })} /></label>
                  <label>Observacoes<textarea value={editForm.notes} onChange={(event) => setEditForm({ ...editForm, notes: event.target.value })} /></label>
                  {editError ? <div className="formError">{editError}</div> : null}
                  <div className="rowActions"><button type="submit">Salvar</button><button type="button" onClick={cancelEdit}>Cancelar</button></div>
                </form>
              ) : null}
            </div>
          ))}
          {filtered.length === 0 ? <EmptyState text="Nenhum atendimento para os filtros selecionados." /> : null}
        </div>
      </Panel>
      <Panel title="Novo atendimento">
        <form className="stackForm" onSubmit={createAppointment}>
          <label>
            Paciente
            <select value={form.patient_id} onChange={(event) => setForm({ ...form, patient_id: event.target.value })}>
              {data.patients.map((patient) => (
                <option key={patient.id} value={patient.id}>{patient.full_name}</option>
              ))}
            </select>
          </label>
          <label>
            Psicologo
            <select value={form.psychologist_id} onChange={(event) => setForm({ ...form, psychologist_id: event.target.value })}>
              {data.psychologists.map((psychologist) => (
                <option key={psychologist.id} value={psychologist.id}>{psychologist.full_name}</option>
              ))}
            </select>
          </label>
          <div className="inlineFields">
            <label>
              Data
              <input type="date" value={form.scheduled_date} onChange={(event) => setForm({ ...form, scheduled_date: event.target.value })} />
            </label>
            <label>
              Hora
              <input type="time" value={form.scheduled_time} onChange={(event) => setForm({ ...form, scheduled_time: event.target.value })} />
            </label>
          </div>
          <label>
            Duracao
            <input value={form.duration_minutes} onChange={(event) => setForm({ ...form, duration_minutes: event.target.value })} />
          </label>
          <label>
            Observacoes
            <textarea value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} />
          </label>
          <button className="primaryButton">
            <Plus size={18} />
            Criar atendimento
          </button>
        </form>
      </Panel>
    </div>
  );
}

function ClinicalRecords({ data, submit }) {
  const [selectedPatientId, setSelectedPatientId] = useState(data.patients[0]?.id || "");
  const [form, setForm] = useState({
    psychologist_id: data.psychologists[0]?.id || "",
    appointment_date: `${today}T09:00`,
    main_complaint: "",
    session_goals: "",
    observed_mood: "",
    clinical_evolution: "",
    interventions: "",
    referrals: "",
    next_steps: "",
    private_notes: "",
    clinical_hypotheses: "",
    therapeutic_plan: "",
    future_attachments: ""
  });
  const selectedPatient = data.patients.find((patient) => patient.id === Number(selectedPatientId));
  const records = data.records.filter((record) => record.patient_id === Number(selectedPatientId));

  const saveRecord = async (event) => {
    event.preventDefault();
    await submit("/clinical-records", {
      patient_id: Number(selectedPatientId),
      psychologist_id: Number(form.psychologist_id),
      appointment_date: `${form.appointment_date}:00`,
      main_complaint: form.main_complaint,
      session_goals: form.session_goals,
      observed_mood: form.observed_mood,
      clinical_evolution: form.clinical_evolution,
      interventions: form.interventions,
      referrals: form.referrals,
      next_steps: form.next_steps,
      private_notes: form.private_notes,
      clinical_hypotheses: form.clinical_hypotheses,
      therapeutic_plan: form.therapeutic_plan,
      future_attachments: form.future_attachments
    });
  };

  return (
    <div className="recordLayout">
      <Panel title="Pacientes">
        <div className="compactList">
          {data.patients.map((patient) => (
            <button
              key={patient.id}
              className={patient.id === Number(selectedPatientId) ? "compactItem selected" : "compactItem"}
              onClick={() => setSelectedPatientId(patient.id)}
            >
              <strong>{patient.full_name}</strong>
              <span>{patient.cpf}</span>
            </button>
          ))}
        </div>
      </Panel>
      <Panel title={selectedPatient ? `Ficha de atendimento - ${selectedPatient.full_name}` : "Ficha de atendimento"}>
        <form className="recordEditor" onSubmit={saveRecord}>
          <div className="inlineFields">
            <label>
              Psicologo responsavel
              <select value={form.psychologist_id} onChange={(event) => setForm({ ...form, psychologist_id: event.target.value })}>
                {data.psychologists.map((psychologist) => (
                  <option key={psychologist.id} value={psychologist.id}>{psychologist.full_name}</option>
                ))}
              </select>
            </label>
            <label>
              Data do atendimento
              <input type="datetime-local" value={form.appointment_date} onChange={(event) => setForm({ ...form, appointment_date: event.target.value })} />
            </label>
          </div>
          <div className="recordSectionTitle">Dados da sessao</div>
          <label>
            Queixa principal
            <textarea value={form.main_complaint} onChange={(event) => setForm({ ...form, main_complaint: event.target.value })} />
          </label>
          <div className="inlineFields">
            <label>
              Objetivos da sessao
              <textarea value={form.session_goals} onChange={(event) => setForm({ ...form, session_goals: event.target.value })} />
            </label>
            <label>
              Humor/estado observado
              <textarea value={form.observed_mood} onChange={(event) => setForm({ ...form, observed_mood: event.target.value })} />
            </label>
          </div>
          <div className="recordSectionTitle">Registro clinico</div>
          <label>
            Evolucao clinica
            <textarea value={form.clinical_evolution} onChange={(event) => setForm({ ...form, clinical_evolution: event.target.value })} />
          </label>
          <div className="inlineFields">
            <label>
              Intervencoes/conduta
              <textarea value={form.interventions} onChange={(event) => setForm({ ...form, interventions: event.target.value })} />
            </label>
            <label>
              Encaminhamentos
              <textarea value={form.referrals} onChange={(event) => setForm({ ...form, referrals: event.target.value })} />
            </label>
          </div>
          <div className="recordSectionTitle">Planejamento</div>
          <div className="inlineFields">
            <label>
              Hipoteses clinicas
              <textarea value={form.clinical_hypotheses} onChange={(event) => setForm({ ...form, clinical_hypotheses: event.target.value })} />
            </label>
            <label>
              Plano terapeutico
              <textarea value={form.therapeutic_plan} onChange={(event) => setForm({ ...form, therapeutic_plan: event.target.value })} />
            </label>
          </div>
          <label>
            Proximos passos
            <textarea value={form.next_steps} onChange={(event) => setForm({ ...form, next_steps: event.target.value })} />
          </label>
          <div className="recordSectionTitle">Uso restrito do psicologo</div>
          <label>
            Observacoes privadas
            <textarea value={form.private_notes} onChange={(event) => setForm({ ...form, private_notes: event.target.value })} />
          </label>
          <button className="primaryButton">
            <CheckCircle2 size={18} />
            Salvar ficha de atendimento
          </button>
        </form>
        <div className="timeline">
          {records.map((record) => (
            <article key={record.id} className="timelineItem">
              <strong>{new Date(record.appointment_date).toLocaleString("pt-BR")}</strong>
              <span>{record.main_complaint || "Queixa principal nao informada."}</span>
              <p>{record.clinical_evolution || "Sem evolucao registrada."}</p>
              <span>{record.interventions || "Conduta nao informada."}</span>
              <span>{record.next_steps || record.therapeutic_plan || "Proximos passos nao informados."}</span>
            </article>
          ))}
          {records.length === 0 ? <EmptyState text="Nenhuma evolucao registrada para este paciente." /> : null}
        </div>
      </Panel>
    </div>
  );
}

function Finance({ data, submit, loadFinance, user }) {
  const [period, setPeriod] = useState({
    cashStart: defaultPeriodStart,
    cashEnd: defaultPeriodEnd,
    accrualStart: defaultCompetencePeriod,
    accrualEnd: defaultCompetenceEnd,
    regime: "cash"
  });
  const [formError, setFormError] = useState("");
  const [paymentForm, setPaymentForm] = useState({
    patient_id: data.patients[0]?.id || "",
    competence_period: defaultCompetencePeriod,
    due_date: today,
    amount: "180,00",
    payment_method: "",
    description: "Sessao individual"
  });
  const [expenseForm, setExpenseForm] = useState({
    description: "",
    amount: "",
    expense_date: today,
    competence_period: defaultCompetencePeriod,
    category_id: ""
  });
  const patientById = Object.fromEntries(data.patients.map((patient) => [patient.id, patient]));

  const savePayment = async (event) => {
    event.preventDefault();
    setFormError("");
    try {
      const { competence_period: competencePeriod, amount, ...fields } = paymentForm;
      await submit("/finance/payments", {
        ...fields,
        ...parseCompetencePeriod(competencePeriod),
        patient_id: Number(paymentForm.patient_id),
        amount_cents: parseMoneyToCents(amount)
      });
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Nao foi possivel criar a cobranca.");
    }
  };

  const saveExpense = async (event) => {
    event.preventDefault();
    setFormError("");
    try {
      const { competence_period: competencePeriod, amount, ...fields } = expenseForm;
      await submit("/finance/expenses", {
        ...fields,
        ...parseCompetencePeriod(competencePeriod),
        category_id: Number(expenseForm.category_id),
        amount_cents: parseMoneyToCents(amount)
      });
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Nao foi possivel criar a despesa.");
    }
  };

  const paymentAction = async (payment, action) => {
    const reason = action === "pay" ? null : window.prompt(action === "reverse" ? "Motivo do estorno" : "Motivo do cancelamento");
    if (action !== "pay" && !reason?.trim()) return;
    const payload = action === "pay" ? { paid_at: today, payment_method: "Pix" } : { reason: reason.trim() };
    try {
      await submit(`/finance/payments/${payment.id}/${action}`, payload, "POST", { "If-Match": `"${payment.version}"` });
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Acao financeira nao concluida.");
    }
  };

  const cancelExpense = async (expense) => {
    const reason = window.prompt("Motivo do cancelamento da despesa");
    if (!reason?.trim()) return;
    try {
      await submit(`/finance/expenses/${expense.id}/cancel`, { reason: reason.trim() }, "POST", { "If-Match": `"${expense.version}"` });
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Cancelamento nao concluido.");
    }
  };

  return (
    <div className="financeLayout">
      <Panel title="Periodo financeiro explicito">
        <form className="inlineFields" onSubmit={(event) => { event.preventDefault(); loadFinance(period); }}>
          <label>
            Inicio inclusivo
            {period.regime === "cash"
              ? <input type="date" value={period.cashStart} onChange={(event) => setPeriod({ ...period, cashStart: event.target.value })} />
              : <input type="month" value={period.accrualStart} onChange={(event) => setPeriod({ ...period, accrualStart: event.target.value })} />}
          </label>
          <label>
            Fim exclusivo
            {period.regime === "cash"
              ? <input type="date" value={period.cashEnd} onChange={(event) => setPeriod({ ...period, cashEnd: event.target.value })} />
              : <input type="month" value={period.accrualEnd} onChange={(event) => setPeriod({ ...period, accrualEnd: event.target.value })} />}
          </label>
          <label>
            Regime
            <select value={period.regime} onChange={(event) => setPeriod({ ...period, regime: event.target.value })}>
              <option value="cash">Caixa (paid_at)</option>
              <option value="accrual">Competencia mensal (AAAA-MM)</option>
            </select>
          </label>
          <button className="primaryButton" disabled={data.loading}>Aplicar periodo</button>
        </form>
        <p>Consulta atual: {data.finance.regime === "cash" ? "Caixa" : "Competencia"}, [{data.finance.start}, {data.finance.end}).</p>
        {data.loading ? <div className="emptyState">Carregando dados financeiros...</div> : null}
        {data.financeError ? <div className="formError">{data.financeError}</div> : null}
        {formError ? <div className="formError">{formError}</div> : null}
      </Panel>
      <div className="metricGrid">
        <Metric title={data.finance.regime === "cash" ? "Recebido em caixa" : "Receita por competencia"} value={money(data.finance.income_cents)} icon={BadgeDollarSign} />
        <Metric title="A receber por competencia" value={money(data.finance.receivable_cents)} icon={CalendarDays} />
        <Metric title={data.finance.regime === "cash" ? "Despesas de caixa" : "Despesas por competencia"} value={money(data.finance.expense_cents)} icon={ClipboardList} />
        <Metric title={`Saldo (${data.finance.regime === "cash" ? "caixa" : "competencia"})`} value={money(data.finance.balance_cents)} icon={ChartNoAxesColumnIncreasing} />
      </div>
      <div className="splitGrid">
        <Panel title="Nova cobranca manual">
          <form className="stackForm" onSubmit={savePayment}>
            <label>
              Paciente
              <select value={paymentForm.patient_id} onChange={(event) => setPaymentForm({ ...paymentForm, patient_id: event.target.value })}>
                {data.patients.map((patient) => (
                  <option key={patient.id} value={patient.id}>{patient.full_name}</option>
                ))}
              </select>
            </label>
            <div className="inlineFields">
              <label>
                Competencia
                <input type="month" value={paymentForm.competence_period} onChange={(event) => setPaymentForm({ ...paymentForm, competence_period: event.target.value })} />
              </label>
              <label>
                Vencimento
                <input type="date" value={paymentForm.due_date} onChange={(event) => setPaymentForm({ ...paymentForm, due_date: event.target.value })} />
              </label>
              <label>
                Valor
                <input value={paymentForm.amount} onChange={(event) => setPaymentForm({ ...paymentForm, amount: event.target.value })} />
              </label>
            </div>
            <div className="inlineFields">
              <label>
                Forma
                <input value={paymentForm.payment_method} onChange={(event) => setPaymentForm({ ...paymentForm, payment_method: event.target.value })} />
              </label>
            </div>
            <label>
              Descricao
              <input value={paymentForm.description} onChange={(event) => setPaymentForm({ ...paymentForm, description: event.target.value })} />
            </label>
            <button className="primaryButton">
              <Plus size={18} />
              Criar cobranca pendente
            </button>
          </form>
        </Panel>
        {user.role === "admin" ? <Panel title="Nova despesa">
          <form className="stackForm" onSubmit={saveExpense}>
            <label>
              Descricao
              <input value={expenseForm.description} onChange={(event) => setExpenseForm({ ...expenseForm, description: event.target.value })} />
            </label>
            <div className="inlineFields">
              <label>
                Competencia
                <input type="month" value={expenseForm.competence_period} onChange={(event) => setExpenseForm({ ...expenseForm, competence_period: event.target.value })} />
              </label>
              <label>
                Data
                <input type="date" value={expenseForm.expense_date} onChange={(event) => setExpenseForm({ ...expenseForm, expense_date: event.target.value })} />
              </label>
              <label>
                Valor
                <input value={expenseForm.amount} onChange={(event) => setExpenseForm({ ...expenseForm, amount: event.target.value })} />
              </label>
            </div>
            <label>
              Categoria
              <select value={expenseForm.category_id} onChange={(event) => setExpenseForm({ ...expenseForm, category_id: event.target.value })} required>
                <option value="">Selecione</option>
                {data.categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
              </select>
            </label>
            <button className="primaryButton">
              <Plus size={18} />
              Lancar despesa
            </button>
          </form>
        </Panel> : <Panel title="Despesas"><EmptyState text="Administracao de despesas restrita ao perfil administrador." /></Panel>}
      </div>
      <div className="contentGrid">
        <Panel title="Receitas">
          <DataTable
            columns={["Paciente", "Competencia", "Vencimento", "Valor", "Forma", "Status", "Acoes"]}
            rows={data.payments.map((payment) => [
              patientById[payment.patient_id]?.full_name || "Paciente",
              payment.competence_period || formatCompetencePeriod(payment.competence_year, payment.competence_month),
              payment.due_date,
              money(payment.amount_cents),
              payment.payment_method,
              payment.overdue ? "Vencido" : statusLabels[payment.status] || payment.status,
              <div className="tableActions">
                {payment.status === "pending" ? <button onClick={() => paymentAction(payment, "pay")}>Pagar</button> : null}
                {payment.status === "pending" ? <button onClick={() => paymentAction(payment, "cancel")}>Cancelar</button> : null}
                {payment.status === "paid" && user.role === "admin" ? <button onClick={() => paymentAction(payment, "reverse")}>Estornar</button> : null}
              </div>
            ])}
          />
          {!data.loading && data.payments.length === 0 ? <EmptyState text="Nenhuma cobranca no periodo e regime selecionados." /> : null}
        </Panel>
        <Panel title="Despesas">
          <DataTable
            columns={["Descricao", "Competencia", "Data", "Valor", "Categoria", "Status", "Acoes"]}
            rows={data.expenses.map((expense) => [
              expense.description, expense.competence_period || formatCompetencePeriod(expense.competence_year, expense.competence_month), expense.expense_date, money(expense.amount_cents),
              expense.category_name, statusLabels[expense.status] || expense.status,
              user.role === "admin" && expense.status === "active" ? <button onClick={() => cancelExpense(expense)}>Cancelar</button> : ""
            ])}
          />
          {!data.loading && data.expenses.length === 0 ? <EmptyState text="Nenhuma despesa no periodo e regime selecionados." /> : null}
        </Panel>
      </div>
    </div>
  );
}

function Reports({ data }) {
  const reportRows = useMemo(
    () => [
      ["Pacientes ativos", data.patients.filter((item) => item.active).length],
      ["Psicologos ativos", data.psychologists.filter((item) => item.active).length],
      ["Atendimentos cadastrados", data.appointments.length],
      ["Prontuarios registrados", data.records.length],
      ["Receitas cadastradas", data.payments.length],
      ["Despesas cadastradas", data.expenses.length],
      [`Saldo do periodo (${data.finance.regime === "cash" ? "caixa" : "competencia"})`, money(data.finance.balance_cents)]
    ],
    [data]
  );

  return (
    <Panel title="Relatorios">
      <DataTable columns={["Indicador", "Valor"]} rows={reportRows} />
    </Panel>
  );
}

function Users({ data, submit, reload, currentUser }) {
  const [form, setForm] = useState({ name: "", username: "", password: "", role: "reception", active: true });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  const create = async (event) => {
    event.preventDefault();
    setError(""); setMessage(""); setSaving(true);
    try {
      await submit("/users", form);
      setForm({ name: "", username: "", password: "", role: "reception", active: true });
      setMessage("Usuario criado com sucesso.");
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Nao foi possivel criar o usuario.");
    } finally { setSaving(false); }
  };

  const toggleActive = async (user) => {
    if (!window.confirm(`${user.active ? "Desativar" : "Ativar"} o usuario ${user.name}?`)) return;
    setError(""); setMessage("");
    try {
      await submit(`/users/${user.id}`, { active: !user.active }, "PATCH");
      setMessage("Status do usuario atualizado.");
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Nao foi possivel atualizar o usuario.");
    }
  };

  const changeRole = async (user, role) => {
    if (role === user.role || !window.confirm(`Alterar o perfil de ${user.name}?`)) return;
    setError(""); setMessage("");
    try {
      await submit(`/users/${user.id}`, { role }, "PATCH");
      setMessage("Perfil do usuario atualizado.");
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Nao foi possivel atualizar o perfil.");
    }
  };

  return <>
    <Panel title="Gestao de usuarios" action={<button className="iconTextButton" onClick={reload}><RefreshCw size={17} /> Recarregar</button>}>
      <p className="muted">Administracao restrita ao perfil admin. Senhas nunca sao exibidas.</p>
      {error ? <div className="formError" role="alert">{error}</div> : null}
      {message ? <div className="successNotice" role="status">{message}</div> : null}
      <form className="settingsGrid" onSubmit={create}>
        <label>Nome<input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
        <label>Usuario<input required value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} /></label>
        <label>Senha inicial<input required minLength="8" type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} /></label>
        <label>Perfil<select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}><option value="reception">Recepcao</option><option value="psychologist">Psicologo</option><option value="admin">Administrador</option></select></label>
        <button className="primaryButton" disabled={saving}><Plus size={18} />{saving ? "Criando..." : "Criar usuario"}</button>
      </form>
      <DataTable columns={["Nome", "Usuario", "Perfil", "Status", "Acoes"]} rows={data.map((user) => [
        user.name, user.username,
        <select aria-label={`Perfil de ${user.name}`} value={user.role} onChange={(event) => changeRole(user, event.target.value)} disabled={user.id === currentUser.id}>
          <option value="reception">Recepcao</option><option value="psychologist">Psicologo</option><option value="admin">Administrador</option>
        </select>,
        user.active ? "Ativo" : "Inativo",
        <button disabled={user.id === currentUser.id} onClick={() => toggleActive(user)}>{user.active ? "Desativar" : "Ativar"}</button>
      ])} />
      {!data.length ? <EmptyState text="Nenhum usuario cadastrado." /> : null}
    </Panel>
  </>;
}

function Settings({ data, submit }) {
  const [form, setForm] = useState(data || { clinic_name: "", phone: "", email: "", address: "", default_session_value: 0, timezone_name: "America/Sao_Paulo" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const save = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");
    setSaving(true);
    try {
      await submit("/settings", buildSettingsPayload(form), "PUT");
      setMessage("Configuracoes salvas com sucesso.");
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Nao foi possivel salvar as configuracoes.");
    } finally {
      setSaving(false);
    }
  };
  return (
    <Panel title="Configuracoes da clinica">
      <form className="settingsGrid" onSubmit={save}>
        <label>
          Nome da clinica
          <input value={form.clinic_name} onChange={(event) => setForm({ ...form, clinic_name: event.target.value })} />
        </label>
        <label>
          Telefone
          <input value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
        </label>
        <label>
          E-mail
          <input value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
        </label>
        <label>
          Valor padrao da sessao
          <input type="number" min="0" step="0.01" value={form.default_session_value} onChange={(event) => setForm({ ...form, default_session_value: event.target.value })} />
        </label>
        <button className="primaryButton" type="submit" disabled={saving}>
          <CheckCircle2 size={18} />
          {saving ? "Salvando..." : "Salvar configuracoes"}
        </button>
      </form>
      <div className="settingsActions">
        {error ? <div className="formError" role="alert">{error}</div> : null}
        {message ? <div className="successNotice" role="status">{message}</div> : null}
      </div>
    </Panel>
  );
}

function Metric({ title, value, icon: Icon }) {
  return (
    <article className="metricCard">
      <div className="metricIcon">
        <Icon size={22} />
      </div>
      <span>{title}</span>
      <strong>{value}</strong>
    </article>
  );
}

function Panel({ title, children, action }) {
  return (
    <article className="panel">
      <header className="panelHeader">
        <h3>{title}</h3>
        {action}
      </header>
      {children}
    </article>
  );
}

function ToolbarSearch({ value, onChange, placeholder }) {
  return (
    <div className="toolbarSearch">
      <Search size={18} />
      <input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
    </div>
  );
}

function DataTable({ columns, rows }) {
  return (
    <div className="tableWrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row[0]}-${index}`}>
              {row.map((cell, cellIndex) => (
                <td key={`${cell}-${cellIndex}`}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AppointmentList({ appointments, patients, psychologists }) {
  const patientById = Object.fromEntries(patients.map((patient) => [patient.id, patient]));
  const psychologistById = Object.fromEntries(psychologists.map((psychologist) => [psychologist.id, psychologist]));

  return (
    <div className="appointmentList">
      {appointments.map((appointment) => (
        <div className="appointmentItem" key={appointment.id}>
          <div className="timeBlock">
            {new Date(appointment.scheduled_at).toLocaleTimeString("pt-BR", {
              hour: "2-digit",
              minute: "2-digit"
            })}
          </div>
          <div>
            <strong>{patientById[appointment.patient_id]?.full_name || "Paciente"}</strong>
            <span>{psychologistById[appointment.psychologist_id]?.full_name || "Psicologo"}</span>
          </div>
          <span className={`statusTag ${appointment.status}`}>{statusLabels[appointment.status] || appointment.status}</span>
        </div>
      ))}
      {appointments.length === 0 ? <EmptyState text="Nenhum atendimento encontrado." /> : null}
    </div>
  );
}

function InfoRow({ label, value, strong }) {
  return (
    <div className={strong ? "infoRow strong" : "infoRow"}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function EmptyState({ text }) {
  return <div className="emptyState">{text}</div>;
}

function LoadingState() {
  return <div className="statePanel" role="status" aria-live="polite">Carregando dados da Clínica Gabriela...</div>;
}

function ErrorState({ text, onRetry }) {
  return (
    <div className="statePanel errorState" role="alert">
      <strong>API indisponível</strong>
      <span>{text}</span>
      <button className="iconTextButton" onClick={() => onRetry()}>Tentar novamente</button>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);

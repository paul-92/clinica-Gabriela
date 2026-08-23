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
  Plus,
  RefreshCw,
  Search,
  Stethoscope,
  UserRound,
  UsersRound
} from "lucide-react";
import "./styles.css";

const API_BASE = "http://127.0.0.1:8000";

const today = new Date().toISOString().slice(0, 10);

const fallback = {
  dashboard: {
    active_patients: 2,
    active_psychologists: 1,
    appointments_today: 1,
    pending_payments: 720,
    paid_payments: 3240,
    expenses: 1200,
    balance: 2040,
    recent_appointments: []
  },
  patients: [
    {
      id: 1,
      full_name: "Paciente 01",
      cpf: "123.456.789-00",
      phone: "(11) 97777-6666",
      email: "paciente01@email.local",
      active: true
    },
    {
      id: 2,
      full_name: "Paciente 02",
      cpf: "987.654.321-00",
      phone: "(11) 95555-1212",
      email: "paciente02@email.local",
      active: true
    }
  ],
  psychologists: [
    {
      id: 1,
      full_name: "Marilia Gabriela Gaspar",
      crp: "11/20433",
      specialty: "Desenvolvimento Infantil",
      phone: "(11) 98888-7777",
      active: true
    }
  ],
  appointments: [
    {
      id: 1,
      scheduled_at: `${today}T09:00:00`,
      patient_id: 1,
      psychologist_id: 1,
      duration_minutes: 50,
      status: "scheduled",
      notes: "Primeira sessao"
    }
  ],
  records: [
    {
      id: 1,
      patient_id: 1,
      psychologist_id: 1,
      appointment_date: `${today}T09:00:00`,
      main_complaint: "Responsaveis relatam dificuldade de concentracao e organizacao da rotina.",
      session_goals: "Acolher demanda inicial, observar comportamento e orientar rotina familiar.",
      observed_mood: "Colaborativo, com oscilacao de atencao durante atividades longas.",
      clinical_evolution: "Paciente relata melhora do sono e reducao de ansiedade.",
      interventions: "Escuta qualificada, psicoeducacao e atividade ludica de reconhecimento emocional.",
      referrals: "Sem encaminhamentos externos nesta sessao.",
      next_steps: "Manter observacao, envolver responsaveis e revisar combinados na proxima sessao.",
      private_notes: "Observar padrao de evitacao em sessoes futuras.",
      clinical_hypotheses: "Ansiedade generalizada em avaliacao.",
      therapeutic_plan: "Acolhimento, psicoeducacao familiar e acompanhamento do desenvolvimento.",
      future_attachments: ""
    }
  ],
  payments: [
    {
      id: 1,
      patient_id: 1,
      due_date: today,
      amount: 180,
      status: "pending",
      payment_method: "Pix",
      description: "Sessao individual"
    }
  ],
  expenses: [
    {
      id: 1,
      description: "Aluguel da sala",
      amount: 1200,
      expense_date: today,
      category: "Estrutura"
    }
  ],
  finance: {
    paid: 3240,
    pending: 720,
    expenses: 1200,
    balance: 2040
  },
  license: {
    valid: true,
    reason: "fallback",
    message: "Modo local de demonstracao.",
    customer: "Cliente em teste",
    type: "trial",
    expires_at: "",
    days_left: 14
  }
};

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: Home },
  { id: "patients", label: "Pacientes", icon: UsersRound },
  { id: "psychologists", label: "Psicologos", icon: Stethoscope },
  { id: "agenda", label: "Agenda", icon: CalendarDays },
  { id: "records", label: "Prontuario", icon: ClipboardList },
  { id: "finance", label: "Financeiro", icon: BadgeDollarSign },
  { id: "reports", label: "Relatorios", icon: ChartNoAxesColumnIncreasing },
  { id: "settings", label: "Configuracoes", icon: Cog }
];

const statusLabels = {
  scheduled: "Agendado",
  rescheduled: "Remarcado",
  canceled: "Cancelado",
  done: "Realizado",
  pending: "Pendente",
  paid: "Pago"
};

async function request(path, options = {}, fallbackValue = null) {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.json();
  } catch {
    return fallbackValue;
  }
}

function money(value) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL"
  }).format(value || 0);
}

function App() {
  const [user, setUser] = useState(null);
  const [activeView, setActiveView] = useState("dashboard");
  const [state, setState] = useState({
    ...fallback,
    online: false,
    loading: true
  });

  const loadData = async () => {
    setState((current) => ({ ...current, loading: true }));
    const [health, license, dashboard, patients, psychologists, appointments, records, payments, expenses, finance] =
      await Promise.all([
        request("/health", {}, null),
        request("/license/status", {}, fallback.license),
        request("/dashboard/summary", {}, fallback.dashboard),
        request("/patients", {}, fallback.patients),
        request("/psychologists", {}, fallback.psychologists),
        request("/appointments", {}, fallback.appointments),
        request("/clinical-records", {}, fallback.records),
        request("/finance/payments", {}, fallback.payments),
        request("/finance/expenses", {}, fallback.expenses),
        request("/finance/summary", {}, fallback.finance)
      ]);
    setState({
      license,
      dashboard,
      patients,
      psychologists,
      appointments,
      records,
      payments,
      expenses,
      finance,
      online: Boolean(health),
      loading: false
    });
  };

  const submit = async (path, payload, method = "POST") => {
    const result = await request(path, { method, body: JSON.stringify(payload) }, null);
    await loadData();
    return result;
  };

  useEffect(() => {
    loadData();
  }, []);

  if (!user) {
    return <LoginScreen onLogin={setUser} online={state.online} license={state.license} />;
  }

  return (
    <div className="appShell">
      <Sidebar activeView={activeView} setActiveView={setActiveView} user={user} onLogout={() => setUser(null)} />
      <main className="workspace">
        <Topbar online={state.online} loading={state.loading} onRefresh={loadData} activeView={activeView} license={state.license} />
        <ViewRouter activeView={activeView} data={state} submit={submit} reload={loadData} />
      </main>
    </div>
  );
}

function LoginScreen({ onLogin, online, license }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
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
    const result = await request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
    setLoading(false);

    if (result?.authenticated) {
      onLogin(result.user);
      return;
    }
    if (username === "admin" && password === "admin123") {
      onLogin({ name: "Administrador", username: "admin", role: "admin" });
      return;
    }
    setError("Usuario ou senha invalidos.");
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
          {online ? "API conectada" : "Modo local"}
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
        {navItems.map((item) => {
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
          {online ? "API online" : "Dados locais"}
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

function ViewRouter({ activeView, data, submit, reload }) {
  const map = {
    dashboard: <Dashboard data={data} />,
    patients: <Patients data={data} reload={reload} />,
    psychologists: <Psychologists data={data} />,
    agenda: <Agenda data={data} submit={submit} />,
    records: <ClinicalRecords data={data} submit={submit} />,
    finance: <Finance data={data} submit={submit} />,
    reports: <Reports data={data} />,
    settings: <Settings />
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
        <Metric title="A receber" value={money(data.dashboard.pending_payments)} icon={BadgeDollarSign} />
        <Metric title="Saldo mensal" value={money(data.dashboard.balance)} icon={ChartNoAxesColumnIncreasing} />
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
            <InfoRow label="Despesas" value={money(data.dashboard.expenses)} />
            <InfoRow label="Recebido" value={money(data.dashboard.paid_payments)} strong />
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

function Agenda({ data, submit }) {
  const [filters, setFilters] = useState({ targetDate: today, psychologistId: "" });
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
  const filtered = data.appointments.filter((appointment) => {
    const sameDate = appointment.scheduled_at.slice(0, 10) === filters.targetDate;
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
    await submit(`/appointments/${appointment.id}`, { status }, "PUT");
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
                <button onClick={() => changeStatus(appointment, "done")}>Realizar</button>
                <button onClick={() => changeStatus(appointment, "rescheduled")}>Remarcar</button>
                <button onClick={() => changeStatus(appointment, "canceled")}>Cancelar</button>
              </div>
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

function Finance({ data, submit }) {
  const [paymentForm, setPaymentForm] = useState({
    patient_id: data.patients[0]?.id || "",
    due_date: today,
    amount: 180,
    status: "pending",
    payment_method: "Pix",
    description: "Sessao individual"
  });
  const [expenseForm, setExpenseForm] = useState({
    description: "",
    amount: 0,
    expense_date: today,
    category: "Operacional"
  });
  const patientById = Object.fromEntries(data.patients.map((patient) => [patient.id, patient]));

  const savePayment = async (event) => {
    event.preventDefault();
    await submit("/finance/payments", {
      ...paymentForm,
      patient_id: Number(paymentForm.patient_id),
      amount: Number(paymentForm.amount)
    });
  };

  const saveExpense = async (event) => {
    event.preventDefault();
    await submit("/finance/expenses", {
      ...expenseForm,
      amount: Number(expenseForm.amount)
    });
  };

  return (
    <div className="financeLayout">
      <div className="metricGrid">
        <Metric title="Recebido" value={money(data.finance.paid)} icon={BadgeDollarSign} />
        <Metric title="Pendente" value={money(data.finance.pending)} icon={CalendarDays} />
        <Metric title="Despesas" value={money(data.finance.expenses)} icon={ClipboardList} />
        <Metric title="Saldo" value={money(data.finance.balance)} icon={ChartNoAxesColumnIncreasing} />
      </div>
      <div className="splitGrid">
        <Panel title="Nova receita">
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
                Status
                <select value={paymentForm.status} onChange={(event) => setPaymentForm({ ...paymentForm, status: event.target.value })}>
                  <option value="pending">Pendente</option>
                  <option value="paid">Pago</option>
                  <option value="canceled">Cancelado</option>
                </select>
              </label>
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
              Lancar receita
            </button>
          </form>
        </Panel>
        <Panel title="Nova despesa">
          <form className="stackForm" onSubmit={saveExpense}>
            <label>
              Descricao
              <input value={expenseForm.description} onChange={(event) => setExpenseForm({ ...expenseForm, description: event.target.value })} />
            </label>
            <div className="inlineFields">
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
              <input value={expenseForm.category} onChange={(event) => setExpenseForm({ ...expenseForm, category: event.target.value })} />
            </label>
            <button className="primaryButton">
              <Plus size={18} />
              Lancar despesa
            </button>
          </form>
        </Panel>
      </div>
      <div className="contentGrid">
        <Panel title="Receitas">
          <DataTable
            columns={["Paciente", "Vencimento", "Valor", "Forma", "Status"]}
            rows={data.payments.map((payment) => [
              patientById[payment.patient_id]?.full_name || "Paciente",
              payment.due_date,
              money(payment.amount),
              payment.payment_method,
              statusLabels[payment.status] || payment.status
            ])}
          />
        </Panel>
        <Panel title="Despesas">
          <DataTable
            columns={["Descricao", "Data", "Valor", "Categoria"]}
            rows={data.expenses.map((expense) => [expense.description, expense.expense_date, money(expense.amount), expense.category])}
          />
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
      ["Saldo mensal", money(data.finance.balance)]
    ],
    [data]
  );

  return (
    <Panel title="Relatorios">
      <DataTable columns={["Indicador", "Valor"]} rows={reportRows} />
    </Panel>
  );
}

function Settings() {
  return (
    <Panel title="Configuracoes da clinica">
      <div className="settingsGrid">
        <label>
          Nome da clinica
          <input defaultValue="Marilia Gabriela Gaspar | Psicologa" />
        </label>
        <label>
          Telefone
          <input defaultValue="(11) 3000-0000" />
        </label>
        <label>
          E-mail
          <input defaultValue="contato@clinicapsi.local" />
        </label>
        <label>
          Valor padrao da sessao
          <input defaultValue="180,00" />
        </label>
      </div>
      <div className="settingsActions">
        <button className="primaryButton">
          <CheckCircle2 size={18} />
          Salvar configuracoes
        </button>
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

createRoot(document.getElementById("root")).render(<App />);

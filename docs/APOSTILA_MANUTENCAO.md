# Apostila de Manutencao do Sistema Marilia Gabriela Gaspar

Esta apostila foi escrita para uma pessoa iniciante que quer entender, manter e evoluir o sistema aos poucos.

O objetivo nao e decorar tudo. O objetivo e voce aprender a se localizar, saber onde mexer, entender por que cada camada existe e ganhar seguranca para fazer pequenas alteracoes sem quebrar o sistema inteiro.

## 1. Visao geral

O projeto possui tres partes principais:

- Desktop Python: uma interface simples feita com Tkinter.
- Backend FastAPI: a API que conversa com o banco SQLite.
- Frontend Electron + React: a interface moderna do sistema.

No dia a dia, a versao recomendada e:

```bat
run_all.bat
```

Esse arquivo abre:

- A API FastAPI.
- A interface Electron + React.

A versao Python simples pode ser aberta com:

```bat
run_desktop.bat
```

## 2. O que acontece quando o sistema abre

Quando voce executa `run_all.bat`, a ideia e esta:

```text
Usuario clica em run_all.bat
        |
        v
scripts/run_all.ps1
        |
        |-- abre a API FastAPI em http://127.0.0.1:8000
        |
        |-- abre o frontend Electron + React
                |
                v
        Tela faz chamadas para a API
                |
                v
        API le e grava dados no SQLite
```

Em palavras simples:

- O Electron mostra as telas.
- O React monta os botoes, formularios e tabelas.
- A API recebe pedidos como "listar pacientes" ou "criar atendimento".
- O SQLite guarda os dados em arquivo local.

## 3. Mapa de pastas

Estrutura principal:

```text
clinica_psicologia_desktop/
  app/
  backend/
  frontend/
  scripts/
  docs/
  tests/
  data/
  main.py
  requirements.txt
  INSTALAR_TUDO.bat
  run_all.bat
```

O que cada pasta faz:

```text
app/
```

Contem a versao desktop Python com Tkinter.

```text
backend/
```

Contem a API FastAPI, os models, schemas, repositories, services e banco SQLite da API.

```text
frontend/
```

Contem a interface Electron + React.

```text
scripts/
```

Contem scripts Windows para instalar, executar e gerar build.

```text
docs/
```

Contem documentacao do projeto.

```text
tests/
```

Contem testes automatizados.

## 4. Conceitos fundamentais

Antes de mexer no codigo, entenda estas palavras.

### API

API e uma ponte. A tela pede algo para a API, e a API responde.

Exemplo:

```text
Tela: "me de a lista de pacientes"
API: "aqui esta a lista"
```

No sistema, a API fica no backend FastAPI.

### Banco de dados

O banco guarda os dados.

Neste projeto, usamos SQLite. Ele e simples e fica em um arquivo local.

Exemplos de dados guardados:

- Pacientes.
- Psicologos.
- Atendimentos.
- Prontuarios.
- Pagamentos.
- Despesas.

### Model

Model representa uma tabela do banco.

Exemplo:

```text
Patient
```

Representa a tabela de pacientes.

### Schema

Schema define o formato dos dados que entram e saem da API.

Exemplo:

```text
PatientCreate
```

Define quais campos a API espera quando alguem cria um paciente.

### Repository

Repository e a camada que conversa diretamente com o banco.

Exemplo:

```text
PatientRepository
```

Sabe buscar, criar e listar pacientes no SQLite.

### Service

Service contem a regra de negocio.

Exemplo:

```text
AppointmentService
```

Valida se o status do atendimento e permitido antes de salvar.

### Route

Route e o endereco HTTP da API.

Exemplo:

```text
GET /patients
```

Lista pacientes.

```text
POST /appointments
```

Cria um atendimento.

## 5. Por que separar em camadas

Separar o sistema em camadas deixa a manutencao mais facil.

Pense assim:

```text
Tela
  chama
API Route
  chama
Service
  chama
Repository
  chama
Banco
```

Cada parte tem uma responsabilidade:

- Tela: mostrar informacoes e receber cliques.
- Route: receber a requisicao HTTP.
- Service: aplicar regra de negocio.
- Repository: acessar o banco.
- Model: representar tabela.
- Schema: validar entrada e saida.

Isso evita misturar tudo em um arquivo so.

## 6. Instalacao

O arquivo mais importante para instalar tudo e:

```bat
INSTALAR_TUDO.bat
```

Ele chama:

```text
scripts/install_all_windows.ps1
```

O que ele faz:

```text
1. Verifica se Python existe.
2. Se nao existir, tenta instalar com winget.
3. Cria o ambiente virtual .venv.
4. Instala as dependencias Python.
5. Inicializa os bancos SQLite.
6. Verifica se npm existe.
7. Se nao existir, tenta instalar Node.js LTS.
8. Instala as dependencias do frontend.
9. Roda testes basicos.
```

### Explicando o arquivo INSTALAR_TUDO.bat

Arquivo:

```text
INSTALAR_TUDO.bat
```

Trecho:

```bat
@echo off
```

Evita que o Windows mostre cada comando antes de executar. Deixa a tela mais limpa.

```bat
setlocal
```

Faz as variaveis usadas no script ficarem restritas ao script.

```bat
title Instalador - Marilia Gabriela Gaspar
```

Define o titulo da janela.

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_all_windows.ps1"
```

Esta e a linha principal.

Ela abre o PowerShell e manda executar o instalador real.

Explicando partes:

- `powershell`: chama o PowerShell.
- `-NoProfile`: abre sem configuracoes pessoais do usuario.
- `-ExecutionPolicy Bypass`: permite executar o script mesmo se o Windows bloquear scripts por padrao.
- `-File`: informa qual arquivo executar.
- `%~dp0`: significa "a pasta onde este .bat esta".

## 7. Execucao no dia a dia

Depois de instalar, voce normalmente usa:

```bat
run_all.bat
```

Esse arquivo chama:

```text
scripts/run_all.ps1
```

O que ele faz:

```text
1. Abre a API em uma janela.
2. Aguarda alguns segundos.
3. Abre o Electron em outra janela.
```

Se quiser abrir so a API:

```bat
run_api.bat
```

Se quiser abrir so a interface Electron:

```bat
run_frontend.bat
```

Se quiser abrir a versao Python simples:

```bat
run_desktop.bat
```

## 8. Backend FastAPI

O backend fica em:

```text
backend/
```

Estrutura:

```text
backend/
  main.py
  api/routes/
  database/
  models/
  schemas/
  repositories/
  services/
  utils/
```

### 8.1 Arquivo backend/main.py

Este arquivo cria a API.

Trecho importante:

```python
from fastapi import FastAPI
```

Importa a classe `FastAPI`, que e usada para criar o servidor da API.

```python
from backend.database.seed import seed_database
from backend.database.session import init_db
```

Importa funcoes que preparam o banco.

- `init_db`: cria as tabelas.
- `seed_database`: cria dados iniciais.

```python
def create_app() -> FastAPI:
```

Cria uma funcao que monta e devolve a aplicacao FastAPI.

O `-> FastAPI` e uma dica de tipo. Ele diz que essa funcao retorna um objeto FastAPI.

```python
init_db()
seed_database()
```

Quando a API sobe, ela garante que o banco exista e tenha dados iniciais.

```python
app = FastAPI(
    title="Marilia Gabriela Gaspar API",
    version="0.1.0",
    description="Backend FastAPI com SQLite para sistema de clinica de psicologia.",
)
```

Cria a API com titulo, versao e descricao.

Esses dados aparecem na documentacao automatica:

```text
http://127.0.0.1:8000/docs
```

```python
@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
```

Cria um endpoint simples para testar se a API esta viva.

Quando alguem acessa:

```text
GET /health
```

A resposta e:

```json
{"status": "ok"}
```

```python
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(patients.router)
```

Adiciona grupos de rotas na API.

Em vez de deixar todos os endpoints dentro de `main.py`, cada modulo tem seu arquivo.

### 8.2 Banco de dados

Arquivo:

```text
backend/database/session.py
```

Esse arquivo configura o SQLite e o SQLAlchemy.

Trecho:

```python
from pathlib import Path
```

Importa uma ferramenta moderna para lidar com caminhos de arquivos.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
```

Importa ferramentas do SQLAlchemy.

- `create_engine`: cria a conexao com o banco.
- `declarative_base`: base usada pelos models.
- `sessionmaker`: cria sessoes de banco.

```python
BASE_DIR = Path(__file__).resolve().parents[1]
```

Pega a pasta base do backend.

```python
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
```

Define a pasta `backend/data` e cria a pasta se ela nao existir.

```python
DATABASE_PATH = DATA_DIR / "clinica_api.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
```

Define o arquivo do banco SQLite.

```python
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
    future=True,
)
```

Cria a conexao com o banco.

Explicando:

- `DATABASE_URL`: caminho do banco.
- `check_same_thread=False`: permite uso com FastAPI.
- `echo=False`: nao imprime SQL no terminal.
- `future=True`: usa estilo mais moderno do SQLAlchemy.

```python
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
```

Cria uma fabrica de sessoes.

Sessao e o objeto usado para consultar e salvar dados.

```python
Base = declarative_base()
```

Cria a classe base usada por todos os models.

```python
def init_db():
```

Funcao que cria as tabelas.

```python
Base.metadata.create_all(bind=engine)
```

Manda o SQLAlchemy criar no banco todas as tabelas definidas nos models.

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Essa funcao entrega uma sessao de banco para cada requisicao da API.

O `yield` entrega o banco para a rota usar.

O `finally` garante que a sessao sera fechada no final.

## 9. Models

Models ficam em:

```text
backend/models/
```

Exemplo:

```text
backend/models/patient.py
```

Trecho:

```python
class Patient(Base):
```

Cria a classe `Patient`, que representa pacientes no banco.

```python
__tablename__ = "patients"
```

Define o nome da tabela no SQLite.

```python
id: Mapped[int] = mapped_column(Integer, primary_key=True)
```

Cria a coluna `id`.

Explicando:

- `Integer`: numero inteiro.
- `primary_key=True`: identifica cada registro de forma unica.

```python
full_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
```

Cria a coluna do nome completo.

- `String(160)`: texto com ate 160 caracteres.
- `nullable=False`: campo obrigatorio.
- `index=True`: ajuda buscas por nome.

```python
cpf: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
```

Cria o CPF.

- `unique=True`: nao permite CPF repetido.

```python
active: Mapped[bool] = mapped_column(Boolean, default=True)
```

Indica se o paciente esta ativo.

## 10. Schemas

Schemas ficam em:

```text
backend/schemas/
```

Eles usam Pydantic.

Exemplo:

```text
backend/schemas/patient.py
```

Trecho:

```python
class PatientBase(ORMBase):
```

Define campos comuns do paciente.

```python
full_name: str
cpf: str
birth_date: date | None = None
```

Define os tipos dos campos.

Explicando:

- `str`: texto.
- `date`: data.
- `date | None`: pode ser data ou vazio.
- `= None`: valor padrao vazio.

```python
class PatientCreate(PatientBase):
    pass
```

Define o formato para criar paciente.

`pass` significa: "nao preciso adicionar nada agora".

```python
class PatientUpdate(ORMBase):
    full_name: str | None = None
```

Define o formato para atualizar paciente.

Os campos sao opcionais porque, ao atualizar, voce pode mudar so um campo.

```python
class PatientRead(PatientBase):
    id: int
```

Define o formato de resposta da API.

Ao ler um paciente, a API devolve tambem o `id`.

## 11. Repositories

Repositories ficam em:

```text
backend/repositories/
```

Eles acessam o banco.

### 11.1 BaseRepository

Arquivo:

```text
backend/repositories/base_repository.py
```

Trecho:

```python
class BaseRepository:
```

Cria uma classe base reutilizavel.

```python
def __init__(self, db, model):
    self.db = db
    self.model = model
```

Guarda a sessao do banco e o model.

```python
def list_all(self):
    return self.db.query(self.model).all()
```

Lista todos os registros da tabela.

```python
def get(self, record_id):
    return self.db.get(self.model, record_id)
```

Busca um registro pelo ID.

```python
def create(self, data):
    entity = self.model(**data)
```

Cria um objeto do model usando os dados recebidos.

O `**data` espalha o dicionario nos campos.

Exemplo:

```python
{"full_name": "Maria", "cpf": "123"}
```

vira algo parecido com:

```python
Patient(full_name="Maria", cpf="123")
```

```python
self.db.add(entity)
self.db.commit()
self.db.refresh(entity)
return entity
```

Explicando:

- `add`: prepara para salvar.
- `commit`: confirma no banco.
- `refresh`: atualiza o objeto com dados gerados pelo banco, como ID.
- `return`: devolve o objeto salvo.

## 12. Services

Services ficam em:

```text
backend/services/
```

Eles contem a regra de negocio.

Exemplo:

```text
backend/services/appointment_service.py
```

Trecho:

```python
class AppointmentService:
```

Classe que cuida dos atendimentos.

```python
def create_appointment(self, data):
    self._validate_status(data.get("status", AppointmentStatus.SCHEDULED.value))
    return self.repository.create(data)
```

Antes de criar, valida o status.

Isso evita salvar status errado no banco.

```python
def _validate_status(self, status_value):
    allowed = {item.value for item in AppointmentStatus}
```

Cria uma lista de status permitidos.

```python
if status_value not in allowed:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status de atendimento invalido.")
```

Se o status for invalido, a API responde erro 400.

## 13. Routes da API

Routes ficam em:

```text
backend/api/routes/
```

Exemplo:

```text
backend/api/routes/appointments.py
```

Trecho:

```python
router = APIRouter(prefix="/appointments", tags=["appointments"])
```

Cria um grupo de endpoints que comecam com:

```text
/appointments
```

```python
@router.get("", response_model=list[AppointmentRead])
def list_appointments(...):
```

Cria o endpoint:

```text
GET /appointments
```

Ele retorna uma lista de atendimentos.

```python
@router.post("", response_model=AppointmentRead, status_code=201)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
```

Cria o endpoint:

```text
POST /appointments
```

Explicando:

- `payload`: dados enviados pela tela.
- `AppointmentCreate`: schema que valida esses dados.
- `db`: sessao do banco.
- `Depends(get_db)`: pede ao FastAPI para entregar uma sessao.
- `status_code=201`: codigo HTTP de "criado com sucesso".

```python
return AppointmentService(db).create_appointment(payload.model_dump())
```

Chama o service para criar o atendimento.

`model_dump()` transforma o schema Pydantic em dicionario Python.

## 14. Dashboard

O dashboard possui endpoint proprio:

```text
GET /dashboard/summary
```

Arquivo:

```text
backend/services/dashboard_service.py
```

Ele calcula:

- Pacientes ativos.
- Psicologos ativos.
- Atendimentos do dia.
- Pagamentos pendentes.
- Pagamentos recebidos.
- Despesas.
- Saldo.

Fluxo:

```text
frontend chama /dashboard/summary
        |
backend/api/routes/dashboard.py
        |
DashboardService
        |
consulta models e services
        |
retorna JSON para a tela
```

## 15. Financeiro

Endpoints principais:

```text
GET /finance/summary
GET /finance/payments
POST /finance/payments
GET /finance/expenses
POST /finance/expenses
```

No frontend, a tela financeiro permite:

- Ver recebido.
- Ver pendente.
- Ver despesas.
- Ver saldo.
- Lancar receita.
- Lancar despesa.

No backend, os models principais sao:

```text
Payment
Expense
```

`Payment` representa receitas, sessoes pagas ou pendentes.

`Expense` representa gastos da clinica.

## 16. Prontuario

Endpoint principal:

```text
GET /clinical-records
POST /clinical-records
PUT /clinical-records/{record_id}
```

Model:

```text
ClinicalRecord
```

Campos importantes:

- `patient_id`: paciente.
- `psychologist_id`: psicologo responsavel.
- `appointment_date`: data do atendimento.
- `main_complaint`: queixa principal.
- `session_goals`: objetivos da sessao.
- `observed_mood`: humor ou estado observado.
- `clinical_evolution`: evolucao clinica.
- `interventions`: intervencoes e conduta.
- `referrals`: encaminhamentos.
- `next_steps`: proximos passos.
- `private_notes`: observacoes privadas.
- `clinical_hypotheses`: hipoteses clinicas.
- `therapeutic_plan`: plano terapeutico.

Regra importante:

Prontuario e dado sensivel. Em uma evolucao futura, recomenda-se criar:

- Controle de permissao por usuario.
- Auditoria de acesso.
- Criptografia ou protecao extra para dados sensiveis.

## 17. Frontend Electron + React

O frontend fica em:

```text
frontend/
```

Estrutura:

```text
frontend/
  package.json
  index.html
  vite.config.js
  electron/
  src/
```

### 17.1 package.json

Arquivo:

```text
frontend/package.json
```

Ele define comandos e dependencias.

Trecho:

```json
"scripts": {
  "dev": "concurrently \"vite --host 127.0.0.1 --port 5173\" \"wait-on http://127.0.0.1:5173 && electron .\"",
  "build": "vite build",
  "dist": "npm run build && electron-builder --win --x64"
}
```

Explicando:

- `npm run dev`: roda Vite e Electron em modo desenvolvimento.
- `npm run build`: gera arquivos finais da interface.
- `npm run dist`: gera build Windows do Electron.

```json
"react": "^18.3.1"
```

Biblioteca usada para criar a interface.

```json
"electron": "^33.2.1"
```

Permite abrir a interface como aplicativo desktop.

```json
"lucide-react": "^0.468.0"
```

Biblioteca de icones.

## 18. Electron

Arquivo:

```text
frontend/electron/main.cjs
```

Esse arquivo abre a janela desktop.

Trecho:

```javascript
const { app, BrowserWindow } = require("electron");
```

Importa recursos do Electron.

```javascript
const path = require("path");
```

Importa ferramenta para lidar com caminhos.

```javascript
const isDev = !app.isPackaged;
```

Verifica se o app esta em desenvolvimento ou empacotado.

```javascript
const mainWindow = new BrowserWindow({
  width: 1360,
  height: 860,
  minWidth: 1100,
  minHeight: 720
});
```

Cria a janela do sistema.

```javascript
if (isDev) {
  mainWindow.loadURL("http://127.0.0.1:5173");
} else {
  mainWindow.loadFile(path.join(__dirname, "../dist/index.html"));
}
```

Em desenvolvimento, abre o Vite.

No build final, abre os arquivos gerados em `dist`.

## 19. React

Arquivo principal:

```text
frontend/src/main.jsx
```

Esse arquivo contem as telas.

### 19.1 Importacoes

Trecho:

```javascript
import React, { useEffect, useMemo, useState } from "react";
```

Importa React e tres hooks:

- `useState`: cria estado.
- `useEffect`: executa algo quando a tela carrega.
- `useMemo`: memoriza calculos.

```javascript
import { createRoot } from "react-dom/client";
```

Usado para renderizar a aplicacao React dentro do HTML.

```javascript
import "./styles.css";
```

Carrega o CSS da interface.

### 19.2 API_BASE

Trecho:

```javascript
const API_BASE = "http://127.0.0.1:8000";
```

Define o endereco da API.

Se um dia a API mudar de porta, este e um dos lugares que voce verifica.

### 19.3 fallback

Trecho:

```javascript
const fallback = {
  patients: [...],
  psychologists: [...],
  appointments: [...]
};
```

Define dados locais de demonstracao.

Por que isso existe?

Para a interface abrir mesmo se a API estiver desligada.

### 19.4 request

Trecho:

```javascript
async function request(path, options = {}, fallbackValue = null) {
```

Cria uma funcao para chamar a API.

```javascript
const response = await fetch(`${API_BASE}${path}`, {
  headers: { "Content-Type": "application/json" },
  ...options
});
```

Faz a chamada HTTP.

Explicando:

- `fetch`: funcao do navegador para acessar API.
- `${API_BASE}${path}`: junta o endereco base com o endpoint.
- `Content-Type`: avisa que os dados estao em JSON.
- `...options`: permite passar metodo POST, PUT e body.

```javascript
if (!response.ok) {
  throw new Error(`HTTP ${response.status}`);
}
```

Se a resposta nao for sucesso, gera erro.

```javascript
return await response.json();
```

Converte a resposta em objeto JavaScript.

```javascript
catch {
  return fallbackValue;
}
```

Se a API falhar, usa um valor alternativo.

### 19.5 Componente App

Trecho:

```javascript
function App() {
```

Componente principal da interface.

```javascript
const [user, setUser] = useState(null);
```

Cria o estado do usuario logado.

- `user`: valor atual.
- `setUser`: funcao para mudar o usuario.
- `null`: comeca sem usuario.

```javascript
const [activeView, setActiveView] = useState("dashboard");
```

Guarda qual tela esta aberta.

```javascript
const [state, setState] = useState({
  ...fallback,
  online: false,
  loading: true
});
```

Guarda os dados do sistema:

- Pacientes.
- Psicologos.
- Atendimentos.
- Prontuarios.
- Financeiro.
- Se a API esta online.
- Se esta carregando.

### 19.6 loadData

Trecho:

```javascript
const loadData = async () => {
```

Funcao que carrega dados da API.

```javascript
const [health, dashboard, patients, psychologists, appointments, records, payments, expenses, finance] =
  await Promise.all([...]);
```

Chama varios endpoints ao mesmo tempo.

Por que `Promise.all`?

Porque e mais rapido do que chamar um por um.

```javascript
setState({
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
```

Atualiza a tela com os dados recebidos.

### 19.7 Login

Trecho:

```javascript
if (!user) {
  return <LoginScreen onLogin={setUser} online={state.online} />;
}
```

Se nao existe usuario logado, mostra a tela de login.

Depois do login, mostra o sistema.

### 19.8 Sidebar

O componente `Sidebar` mostra o menu lateral.

Ele usa:

```javascript
navItems.map(...)
```

Isso percorre a lista de menus e cria um botao para cada tela.

Se quiser adicionar uma tela nova:

1. Adicione item em `navItems`.
2. Crie o componente da tela.
3. Adicione no `ViewRouter`.

### 19.9 ViewRouter

Trecho:

```javascript
const map = {
  dashboard: <Dashboard data={data} />,
  agenda: <Agenda data={data} submit={submit} />,
  records: <ClinicalRecords data={data} submit={submit} />,
  finance: <Finance data={data} submit={submit} />
};
```

Esse objeto decide qual tela mostrar.

Se `activeView` for `"finance"`, mostra o componente `Finance`.

## 20. CSS

Arquivo:

```text
frontend/src/styles.css
```

O CSS define a aparencia.

Exemplo:

```css
.appShell {
  display: grid;
  grid-template-columns: 280px 1fr;
  min-height: 100vh;
}
```

Explicando:

- `.appShell`: classe do container principal.
- `display: grid`: usa layout em grade.
- `grid-template-columns: 280px 1fr`: primeira coluna tem 280px, segunda ocupa o resto.
- `min-height: 100vh`: altura minima igual a tela inteira.

```css
.sidebar {
  display: flex;
  flex-direction: column;
}
```

Faz o menu lateral organizar os itens de cima para baixo.

```css
.metricGrid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
```

Cria 4 cards de indicadores em linha.

```css
@media (max-width: 1180px) {
```

Cria regras para telas menores.

Isso ajuda em notebooks ou janelas menores.

## 21. Versao desktop Python

Entrada:

```text
main.py
```

Trecho:

```python
from app.database.seed import seed_database
from app.database.session import init_db
from app.views.login_view import LoginView
```

Importa:

- Criacao do banco.
- Dados iniciais.
- Tela de login.

```python
def main():
    init_db()
    seed_database()
    LoginView().run()
```

Quando o desktop Python abre:

1. Cria banco se necessario.
2. Insere dados iniciais se necessario.
3. Mostra a tela de login.

```python
if __name__ == "__main__":
    main()
```

Garante que `main()` sera chamado quando voce executar:

```bat
python main.py
```

## 22. Como fazer manutencao na pratica

### Caso 1: Adicionar campo no paciente

Exemplo: adicionar `profession`.

Passos:

1. Adicionar coluna no model:

```text
backend/models/patient.py
```

2. Adicionar campo nos schemas:

```text
backend/schemas/patient.py
```

3. Ajustar formulario no frontend:

```text
frontend/src/main.jsx
```

4. Se necessario, ajustar tela desktop Python:

```text
app/views/pages.py
```

5. Testar.

Observacao importante:

Como o projeto ainda nao usa migrations, se a tabela ja existir no SQLite, a coluna nova pode nao aparecer automaticamente. Em desenvolvimento, voce pode apagar o banco local e recriar. Em producao, o ideal e adicionar Alembic no futuro.

### Caso 2: Criar novo endpoint

Exemplo: listar aniversariantes.

Passos:

1. Criar metodo no repository, se precisar consultar banco.
2. Criar metodo no service.
3. Criar rota em `backend/api/routes/`.
4. Incluir a rota em `backend/main.py`, se for um arquivo novo.
5. Chamar no frontend com `request("/novo-endpoint")`.

### Caso 3: Alterar uma tela

Se for visual:

```text
frontend/src/styles.css
```

Se for comportamento:

```text
frontend/src/main.jsx
```

Se for dado vindo do banco:

```text
backend/
```

## 23. Como testar

Teste Python:

```bat
.venv\Scripts\python.exe -m pytest tests
```

Teste manual da API:

```bat
run_api.bat
```

Depois abra:

```text
http://127.0.0.1:8000/docs
```

Teste manual do sistema:

```bat
run_all.bat
```

Primeiro acesso em banco novo:

```powershell
$env:INITIAL_ADMIN_USERNAME = "administrador"
$env:INITIAL_ADMIN_PASSWORD = "uma-senha-forte-com-12-ou-mais-caracteres"
```

As credenciais iniciais devem existir apenas no ambiente da primeira execucao e ser removidas depois do provisionamento.

## 24. Erros comuns

### Python nao encontrado

Instale Python 3.11 ou superior.

Depois rode:

```bat
INSTALAR_TUDO.bat
```

### npm nao encontrado

Instale Node.js LTS.

Depois rode:

```bat
INSTALAR_TUDO.bat
```

### API nao abre

Verifique se a porta 8000 ja esta em uso.

Teste:

```bat
run_api.bat
```

### Frontend abre sem dados

Possiveis causas:

- API desligada.
- Porta 8000 bloqueada.
- Banco ainda nao inicializado.

Rode:

```bat
INSTALAR_TUDO.bat
run_all.bat
```

## 25. Cuidados com dados sensiveis

Este sistema lida com dados de pacientes e prontuarios.

Cuidados recomendados:

- Nao compartilhar a pasta do sistema com pessoas nao autorizadas.
- Fazer backup regularmente.
- Proteger o computador com senha.
- Nao enviar o banco por e-mail sem protecao.
- Evoluir o sistema com permissoes mais fortes antes de uso real em clinica.

## 26. Onde ficam os bancos

Desktop Python:

```text
data/clinica_psicologia.db
```

API FastAPI:

```text
backend/data/clinica_api.db
```

## 27. Backup

Existe um script:

```text
scripts/backup_database.py
```

Ele copia o banco desktop para uma pasta de backups.

Para rodar:

```bat
.venv\Scripts\python.exe scripts\backup_database.py
```

Futuramente, recomenda-se criar backup tambem para:

```text
backend/data/clinica_api.db
```

## 28. Build

Para gerar build Windows:

```bat
build_windows.bat
```

Ele chama scripts que tentam gerar:

```text
dist/windows/desktop
frontend/release
```

Explicando:

- `dist/windows/desktop`: build da versao Python.
- `frontend/release`: instalador ou app empacotado do Electron.

## 29. Ordem recomendada para aprender

Se voce esta comecando, siga esta ordem:

1. Leia esta apostila inteira uma vez, sem tentar decorar.
2. Abra `README.md`.
3. Rode `INSTALAR_TUDO.bat`.
4. Rode `run_all.bat`.
5. Abra `http://127.0.0.1:8000/docs`.
6. Teste endpoints na documentacao da API.
7. Abra `frontend/src/main.jsx` e procure `function Dashboard`.
8. Mude um texto pequeno na tela.
9. Mude uma cor no CSS.
10. Crie um paciente pela API.
11. Entenda o fluxo route -> service -> repository -> model.

## 30. Mini glossario

API:
Ponte entre a tela e os dados.

Endpoint:
Endereco da API, como `/patients`.

JSON:
Formato de dados usado para comunicacao entre tela e API.

SQLite:
Banco de dados em arquivo local.

SQLAlchemy:
Biblioteca Python que facilita trabalhar com banco.

FastAPI:
Framework Python para criar APIs.

React:
Biblioteca JavaScript para criar interfaces.

Electron:
Tecnologia que transforma interface web em aplicativo desktop.

Vite:
Ferramenta que roda e gera build do frontend React.

Repository:
Camada que acessa o banco.

Service:
Camada que contem regra de negocio.

Schema:
Contrato de dados da API.

Model:
Representacao da tabela do banco.

## 31. Regra de ouro para manutencao

Quando for mexer em algo, pergunte:

```text
Isso e visual?
```

Va para:

```text
frontend/src/styles.css
frontend/src/main.jsx
```

```text
Isso e regra de negocio?
```

Va para:

```text
backend/services/
```

```text
Isso e banco?
```

Va para:

```text
backend/models/
backend/repositories/
```

```text
Isso e entrada ou saida da API?
```

Va para:

```text
backend/schemas/
backend/api/routes/
```

Com essa separacao, voce evita mexer no lugar errado.

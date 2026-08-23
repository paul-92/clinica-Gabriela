# Arquitetura

O sistema segue uma separacao simples em camadas:

- `views`: telas Tkinter.
- `controllers`: entrada das acoes de interface.
- `services`: regras de negocio.
- `repositories`: acesso ao banco.
- `models`: entidades SQLAlchemy persistidas em SQLite.
- `database`: configuracao, criacao e dados iniciais.

As telas nao acessam o banco diretamente. Elas chamam controllers, que coordenam servicos e repositorios.

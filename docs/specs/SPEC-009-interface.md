# SPEC-009 — Nova Interface Clínica e Design System

Status: DRAFT — baseline visual definida; implementação não iniciada.
Prioridade: P1. Dependências: SPEC-002 e SPEC-008.

## Objetivo
Modernizar a interface Electron/React com identidade acolhedora e profissional da Clínica Gabriela.

## Referências
Cinco imagens fornecidas pelo usuário nesta conversa: identidade MG, dashboard, prontuário e financeiro.
As imagens são referências visuais; não foram incorporadas ao repositório nem reproduzidas neste pacote.

## Direção visual
Verde sálvia, off-white, rosa suave, bege quente, texto escuro, cards arredondados, ícones lineares, espaçamento generoso e tipografia elegante.
Preservar identidade clínica sem copiar cegamente pixels.

## Shell
Sidebar com marca, navegação por perfil, estado ativo e usuário; topbar, status de conexão e conteúdo responsivo.

## Telas
- Dashboard: indicadores, agenda do dia, próximos atendimentos e resumos autorizados.
- Agenda: dia/semana, filtros, status e ações.
- Pacientes: busca, filtros, cadastro e ficha.
- Prontuário: paciente, evoluções, histórico, anexos, plano de metas e documentos; campos privados protegidos.
- Financeiro: receitas, despesas, pendências, saldo, lançamentos e gráficos com contratos corretos.
- Relatórios, Configurações e Usuários conforme APIs e permissões disponíveis.

## Requisitos transversais
- Loading, vazio, erro, offline, não autorizado e sessão expirada.
- Demo explícita e isolada; nunca substituir silenciosamente dados reais.
- Navegação por perfil não substitui autorização backend.
- Acessibilidade, teclado, contraste e estados não dependentes apenas de cor.
- Priorizar Windows 1366×768 e 1920×1080, incluindo escalas comuns.
- Modularizar frontend após inventário da estrutura atual.
- Não duplicar redesign completo no Tkinter.

## Aceitação
Design system consistente, fluxos reais, estados tratados, permissões respeitadas, sem credenciais hardcoded e build aprovado.

## Fora do escopo
Novas regras de negócio, instalador, redesign paralelo do Tkinter e APIs inexistentes.

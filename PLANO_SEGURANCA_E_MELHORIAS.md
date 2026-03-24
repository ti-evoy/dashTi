# Plano de Seguranca e Melhorias

## Objetivo do Documento

Este documento registra os principais riscos do `dashTi`, as recomendacoes de seguranca e um plano de evolucao tecnica para uso corporativo.

## Resumo Executivo

O projeto atende bem um cenario interno de baixa complexidade, com implementacao simples e rapidez de uso. O principal ponto de atencao e que a persistencia em Google Sheets traz limitacoes de concorrencia, auditabilidade e controle transacional.

O plano abaixo foi desenhado para:

- reduzir risco operacional;
- melhorar governanca;
- preparar o sistema para crescimento;
- documentar decisoes para uso interno na empresa.

## Estado Atual

### Pontos positivos

- Interface simples e rapida para o time.
- Baixo custo de implantacao.
- Facil manutencao inicial.
- Dados centralizados em uma planilha compartilhada.

### Limitacoes atuais

- Persistencia em Google Sheets sem controle transacional.
- Controle de acesso simples via token.
- Dependencia forte de uma unica planilha.
- Ausencia de testes automatizados.
- Documentacao antes da atualizacao era insuficiente.

## Principais Riscos

### Risco 1: conflito de gravacao

Se duas pessoas atualizarem a mesma aba quase ao mesmo tempo, a ultima gravacao pode sobrescrever a anterior.

Impacto:

- perda parcial de dados;
- inconsistencias no acompanhamento;
- retrabalho manual.

Mitigacao recomendada:

- curto prazo: orientar uso com menos concorrencia simultanea;
- medio prazo: incluir controle de versao logica por registro;
- longo prazo: migrar para banco relacional.

### Risco 2: controle de acesso fraco

O modelo atual com token em URL ajuda no bloqueio basico, mas nao oferece rastreabilidade, expiração de sessao, MFA ou identidade corporativa.

Impacto:

- compartilhamento indevido do link;
- acesso por pessoas nao autorizadas;
- falta de trilha de auditoria por usuario.

Mitigacao recomendada:

- curto prazo: rotacionar token e restringir distribuicao;
- medio prazo: colocar a aplicacao atras de autenticacao corporativa;
- longo prazo: integrar com SSO.

### Risco 3: indisponibilidade ou erro humano na planilha

Mudancas diretas na planilha por usuarios podem quebrar estrutura, nomes de colunas ou tipos de dados.

Impacto:

- erro na aplicacao;
- falha de leitura;
- perda de confiabilidade do dashboard.

Mitigacao recomendada:

- proteger colunas sensiveis;
- limitar edicao direta da planilha;
- manter backup e controle de restauracao.

### Risco 4: ambiente de desenvolvimento inseguro em uso indevido

O `devcontainer` atual executa o Streamlit com CORS e XSRF desabilitados. Isso e aceitavel para ambiente local e controlado, mas nao deve ser replicado em ambiente corporativo exposto.

Impacto:

- aumento da superficie de ataque;
- risco de uso indevido fora do ambiente esperado.

Mitigacao recomendada:

- manter essa configuracao apenas para desenvolvimento;
- habilitar protecoes em homologacao e producao.

## Plano de Seguranca

## Fase 1: imediata

Prazo sugerido: 1 a 2 semanas

- Criar backup recorrente da planilha principal.
- Restringir compartilhamento do Google Sheets a usuarios autorizados.
- Revisar permissao da service account e manter apenas o minimo necessario.
- Definir responsavel funcional e tecnico pelo sistema.
- Registrar procedimento de restauracao da planilha.
- Validar que o arquivo de secrets nao esta versionado.

## Fase 2: endurecimento

Prazo sugerido: 2 a 4 semanas

- Remover dependencias nao utilizadas.
- Fixar versoes no `requirements.txt`.
- Criar ambiente de homologacao.
- Adicionar logs de erro e eventos operacionais relevantes.
- Implementar validacoes mais fortes de entrada.
- Revisar estrutura de observacoes e historico dos chamados.

## Fase 3: maturidade

Prazo sugerido: 1 a 3 meses

- Adotar autenticacao corporativa.
- Criar trilha de auditoria por usuario.
- Introduzir testes automatizados.
- Extrair regras do `app.py` para servicos/funcoes menores.
- Avaliar migracao do armazenamento para banco relacional.

## Roadmap de Melhorias Tecnicas

### Prioridade alta

- Quebrar `app.py` em modulos por dominio:
  - projetos
  - reunioes
  - sprints
  - chamados
- Criar funcoes auxiliares para formularios e componentes repetidos.
- Fixar versoes das bibliotecas.
- Remover bibliotecas nao utilizadas.

### Prioridade media

- Criar testes unitarios para `utils.py`.
- Criar padrao de tratamento de erros mais consistente.
- Melhorar o README com exemplos de operacao.
- Padronizar nomenclatura de campos e textos.

### Prioridade baixa

- Evoluir visual da interface com componentes mais reutilizaveis.
- Criar exportacoes adicionais.
- Criar indicadores de produtividade e SLA.

## Backlog Recomendado

### Backlog tecnico

- Refatorar `app.py` em arquivos menores.
- Criar camada de servicos para regras de negocio.
- Adicionar linter e formatador.
- Adicionar testes de regressao.

### Backlog funcional

- Pesquisa global por registros.
- Filtros mais detalhados em projetos e chamados.
- Historico de alteracoes.
- Dashboard de tendencias por periodo.

## Procedimentos Operacionais

### Backup

- Periodicidade recomendada: diaria.
- Responsavel: time de TI ou responsavel da area.
- Evidencia: pasta protegida ou processo automatizado.

### Restauracao

- Manter uma copia limpa da planilha.
- Testar restauracao em ambiente controlado.
- Registrar ultimo backup valido.

### Controle de acesso

- Compartilhar app e planilha apenas com pessoas autorizadas.
- Evitar envio de links com token por canais abertos.
- Revisar acessos mensalmente.

## Criterios para Evoluir de Google Sheets

Recomenda-se migrar para banco quando houver:

- aumento de usuarios simultaneos;
- necessidade de auditoria por usuario;
- necessidade de controle transacional;
- exigencia de rastreabilidade formal;
- crescimento do volume de registros.

## Conclusao

O `dashTi` ja atende bem um cenario interno inicial, mas para consolidacao corporativa o proximo passo deve ser fortalecer seguranca, governanca e capacidade de manutencao. A recomendacao e manter Google Sheets no curto prazo, com controles operacionais e refatoracao gradual, e planejar autenticacao corporativa e armazenamento mais robusto no medio prazo.

# Projeto 6 - DevSecOps Watchtower

Guardiao inteligente de vulnerabilidades em tempo real com arquitetura orientada a eventos.

Este projeto simula um fluxo de seguranca em que:

- um produtor gera eventos de log
- uma engine de IA faz triagem e (quando necessario) gera remediacao
- um dashboard exibe tudo em tempo real

## Visao Geral

O repositorio possui **2 stacks completas** de demonstracao:

1. Stack Web (principal): dashboard Flask + SSE, engine com endpoint OpenAI-compatible
2. Stack Terminal (alternativa): dashboard Rich no terminal, engine com Ollama

As duas stacks usam ZeroMQ no padrao PUB/SUB:

- Porta `5555`: stream de logs (`LOG`)
- Porta `5556`: stream de alertas (`ALERT`)

## Arquitetura

### Stack Web (principal)

- `producer.py`: publica logs simulados na porta 5555
- `engine.py`: recebe logs, classifica ameacas com LLM, publica alertas na 5556
- `main.py`: dashboard web Flask, consome 5555 e 5556 e faz streaming via SSE

Fluxo:

1. `producer.py` envia eventos `LOG`
2. `engine.py` analisa o evento com IA
3. se for ameaca, gera `triage` e opcionalmente `remediation`
4. publica pacote `ALERT`
5. `main.py` atualiza a interface em tempo real

### Stack Terminal (alternativa)

- `producer.py`: produtor de logs simulados
- `engine.py`: engine de IA (Ollama)
- `main.py`: dashboard no terminal com Rich

## Requisitos

- Python 3.12+
- Ambiente virtual Python
- ZeroMQ (via `pyzmq`)
- Provedor de LLM conforme stack usada:
	- Stack Web: endpoint OpenAI-compatible (atualmente configurado para LM Studio)
	- Stack Terminal: Ollama local

Dependencias declaradas no projeto:

- flask
- langchain
- langchain-openai
- pydantic
- pyzmq
- tornado

## Instalacao

### Opcao 1: usando `uv` (recomendado)

```bash
uv sync
```

### Opcao 2: usando `pip`

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install flask langchain langchain-openai pydantic pyzmq tornado
```

Para usar a stack terminal, instale tambem:

```bash
pip install rich langchain-ollama
```

## Como Executar

Abra **3 terminais** na raiz do projeto e ative o ambiente virtual em todos.

### Executar Stack Web (principal)

Terminal 1:

```bash
python producer.py
```

Terminal 2:

```bash
python engine.py
```

Terminal 3:

```bash
python main.py
```

Depois acesse no navegador:

```text
http://localhost:5000
```

### Executar Stack Terminal (alternativa)

Terminal 1:

```bash
python producer.py
```

Terminal 2:

```bash
python engine.py
```

Terminal 3:

```bash
python main.py
```

## Configuracao de LLM

### Stack Web (`engine.py`)

A engine esta configurada para usar um endpoint OpenAI-compatible:

- Base URL: `http://172.30.64.1:1234/v1`
- API Key: `lm-studio`
- Modelo: `google/gemma-3-12b`

Se necessario, ajuste esses valores diretamente no arquivo `engine.py`.

## Estrutura de Eventos

### Evento de entrada (`LOG`)

Exemplo (stack web):

```json
{
	"type": "LOG",
	"timestamp": "14:22:10",
	"source": "Web Application Firewall",
	"message": "SQL injection attempt detected"
}
```

### Evento de saida (`ALERT`)

```json
{
	"type": "ALERT",
	"original_event": {"...": "..."},
	"triage": {
		"is_threat": true,
		"severity": "CRITICAL",
		"category": "SQL Injection",
		"reasoning": "Entrada maliciosa detectada"
	},
	"remediation": {
		"action_plan": "Aplicar validacao e queries parametrizadas",
		"code_fix": "cursor.execute('SELECT ... WHERE user = %s', (user,))"
	}
}
```

## Solucao de Problemas

- `Address already in use`:
	- alguma aplicacao ja esta usando a porta 5555, 5556 ou 5000
	- encerre processos antigos e rode novamente

- Dashboard sem eventos:
	- confirme que o producer esta ativo
	- confirme que engine e dashboard estao rodando ao mesmo tempo

- Engine nao gera alerta:
	- verifique conectividade com o provedor de LLM
	- confira se o modelo configurado esta carregado

- Erro de import na stack terminal:
	- instale `rich` e `langchain-ollama`

## Observacoes Importantes

- Nao execute as duas stacks ao mesmo tempo (ambas usam as mesmas portas).
- A stack web usa campo `message` no log; a stack terminal usa `raw_log`.
- O projeto tem foco educacional para estudos de AgentOps, DevSecOps e automacao com IA.

## Licenca

Uso educacional.

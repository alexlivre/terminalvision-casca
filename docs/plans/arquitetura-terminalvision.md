# TerminalVision: Arquitetura MCP + CASCA

> **Meta:** Criar sistema de controle de terminal onde MCP (Python) conecta-se a CASCA (Go) via API.

---

## Conceito

```
┌─────────────┐     API (HTTP/named pipe)     ┌─────────────────┐
│   MCP       │ ◄─────────────────────────────► │   CASCA         │
│  (Python)   │   - send_keys                 │  (Go binary)    │
│             │   - get_screen                │                 │
│  Ferramentas│   - list_sessions             │  Terminal real  │
│  MCP        │   - spawn/kill                │  com screenshot │
└─────────────┘                                └─────────────────┘
```

---

## Componentes

### CASCA (Go)
**Responsabilidade:** Terminal real + API de controle

```
casca/
├── main.go           # Entry point, servidor HTTP
├── terminal.go      # Gerencia processos de terminal
├── screen.go        # Captura screenshot da tela
├── api/
│   └── handlers.go   # Rotas HTTP: /spawn, /send, /screen, /list
├── go.mod
└── Makefile
```

**API Endpoints:**

| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/terminal/spawn` | Cria nova sessão de terminal |
| GET | `/terminal/list` | Lista sessões ativas |
| POST | `/terminal/{id}/send` | Envia teclas |
| GET | `/terminal/{id}/screen` | Screenshot da tela |
| POST | `/terminal/{id}/resize` | Redimensiona |
| DELETE | `/terminal/{id}` | Encerra sessão |

**Request/Response examples:**

```json
// POST /terminal/spawn
Request:  { "command": "cmd.exe", "cols": 120, "rows": 40 }
Response: { "session_id": "abc123", "success": true }

// POST /terminal/{id}/send
Request:  { "keys": "hello\n" }
Response: { "success": true }

// GET /terminal/{id}/screen
Response: { "type": "text", "content": "dir\nC:\\>", "hash": "md5" }
   ou
Response: { "type": "image", "path": "/tmp/screen.png" }
```

**Named Pipe (Windows):**
```
\\.\pipe\terminalvision
```
Ou fallback para HTTP localhost:8787

---

### MCP (Python)
**Responsabilidade:** Servidor MCP + client para CASCA

```
mcp/
├── main.py              # Entry point MCP
├── client/
│   └── casca_client.py   # HTTP client para CASCA
├── tools/
│   ├── terminal_spawn.py
│   ├── terminal_get_screen.py
│   ├── terminal_send_keys.py
│   └── ...
├── types/
│   └── types.py          # Pydantic models (reutilizar)
├── pyproject.toml
└── requirements.txt
```

**Tools MCP:**

| Tool | Descrição |
|------|-----------|
| `terminal_spawn` | Spawn via CASCA |
| `terminal_get_screen` | Captura tela (text/image) |
| `terminal_send_keys` | Envia teclas |
| `terminal_wait_for_stable` | Espera tela estabilizar |
| `terminal_list_sessions` | Lista sessões |
| `terminal_resize` | Redimensiona |
| `terminal_kill` | Encerra |
| `list_vision_mcps` | Descoberta (futuro) |

---

## Fluxo de Operações

### 1. Spawn terminal
```
Qwen Code → terminal_spawn tool
  → MCP main.py → HTTP POST /terminal/spawn
    → CASCA: spawn subprocess (cmd.exe, powershell, cmdit)
    → CASCA: retorna session_id
  → MCP: retorna session_id para Qwen
```

### 2. Get screen
```
Qwen → terminal_get_screen tool (session_id, format=text)
  → MCP → HTTP GET /terminal/{id}/screen
    → CASCA: captura tela
    → CASCA: retorna texto ou path
  → MCP: formata e retorna
```

### 3. Send keys
```
Qwen → terminal_send_keys tool (session_id, keys="Ctrl+C")
  → MCP → HTTP POST /terminal/{id}/send
    → CASCA: parse keys → bytes
    → CASCA: write para stdin do processo
  → MCP: retorna success
```

---

## Stack Tecnológico

| Componente | Linguagem | Biblioteca | Motivo |
|-----------|-----------|------------|--------|
| MCP Server | Python 3.11+ | `mcp` SDK | Padrão MCP |
| CASCA App | Go 1.21+ | net/http | Binário único |
| Terminal | Sistema | subprocess | Nativo |
| Screenshot | Go | github.com/gen2brain/msh | Cross-platform |

---

## Roadmap de Implementação

### Fase 1: CASCA básico (Go)
- [ ] Servidor HTTP minimal
- [ ] Spawn subprocess
- [ ] Captura stdout
- [ ] Send stdin
- [ ] Kill process

### Fase 2: MCP Server (Python)
- [ ] Client HTTP para CASCA
- [ ] Tools MCP básicas
- [ ] Integration test

### Fase 3: Screenshot
- [ ] Parser de texto (VT100)
- [ ] Screenshot real
- [ ] Toggle text/image

### Fase 4: Polimento
- [ ] Named pipe fallback
- [ ] Named pipe primary
- [ ] Estabilidade detection

---

## Arquivo de Configuração

```yaml
# casca.yaml (opcional)
host: "localhost"
port: 8787
pipe: "\\\\.\\pipe\\terminalvision"
default_shell: "cmd.exe"
```

---

## Testes

### CASCA tests (Go)
```bash
go test ./...
```

### MCP tests (Python)
```bash
pytest tests/ -v
```

### Integration tests
```bash
# 1. Start CASCA
./casca --port 8787

# 2. Run MCP
python -m terminalvision_mcp

# 3. Use from Qwen Code
```

---

## Perguntas em Aberto

1. **CASCA como serviço ou por-demand?** (startup automático vs inicia quando MCP precisa)
2. **Persistência de sessões?** (memória vs arquivo)
3. **Auth?** (localhost-only por enquanto, sem auth)
4. **cmdit específico ou genérico?** (foco em cmd.exe primeiro)
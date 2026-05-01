# TerminalVision: Arquitetura MCP + CASCA v3

> **Versão:** 3.0 (Final após research)
> **Data:** 2026-05-01
> **Status:** Para implementação

---

## Resumo Executivo

**Meta:** MCP Server que controla programas de terminal interativos (TUIs) como cmdit, vim, nano.

**Problema:** subprocess.Popen cria pipes, não TTYs. TUIs detectam ausência de TTY e falham.

**Solução:** CASCA (Go) é um daemon que gerencia terminais REAIS (ConPTY/Visible) e expõe API HTTP. MCP (Python) conecta ao CASCA e expõe tools para o agente.

---

## Conceito Visual

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TerminalVision                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   ┌─────────┐        ┌──────────────────────────────────────────┐   │
│   │   MCP   │◄──────►│                   CASCA                    │   │
│   │(Python) │  HTTP  │                  (Go)                     │   │
│   │         │        │                                             │   │
│   │ Tools:  │        │  ┌─────────────────────────────────────┐   │   │
│   │ -spawn  │        │  │         Infrastructure              │   │   │
│   │ -screen │        │  │  ┌─────────────┐ ┌─────────────┐   │   │   │
│   │ -keys   │        │  │  │  ConPTY     │ │  Visible    │   │   │   │
│   │ -resize │        │  │  │  (headless) │ │  (window)   │   │   │   │
│   │ -wait   │        │  │  └─────────────┘ └─────────────┘   │   │   │
│   │ -kill   │        │  │                                     │   │   │
│   │ -list   │        │  │  ┌─────────────┐ ┌─────────────┐   │   │   │
│   └─────────┘        │  │  │  Screenshot │ │  Key Send   │   │   │   │
│                     │  │  │  (VT100/img) │ │  (PTY/WM)   │   │   │   │
│                     │  │  └─────────────┘ └─────────────┘   │   │   │
│                     │  └─────────────────────────────────────┘   │   │
│                     └──────────────────────────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Research: Bibliotecas Identificadas

### ConPTY para Go
| Biblioteca | Uso | Status |
|------------|-----|--------|
| `github.com/qsocket/conpty-go` | ConPTY Windows nativo | **Usar** |
| `github.com/creack/pty` | PTY cross-platform (Unix + ConPTY) | **Usar como fallback** |

### Screenshot
| Biblioteca | Uso | Status |
|------------|-----|--------|
| `github.com/gen2brain/mss` | Screenshot cross-platform | Verificar |
| `github.com/vova616/screenshot` | Alternativa mais leve | Backup |

### HTTP Router
| Biblioteca | Uso | Status |
|------------|-----|--------|
| `net/http` (stdlib) | HTTP server | **Usar** |
| `github.com/gorilla/mux` | Router mais rico | Opcional |

### Referências de Arquitetura
| Projeto | Linguagem | Relevância |
|--------|-----------|------------|
| [agent-tui](https://github.com/pproenca/agent-tui) | Rust | Arquitetura idêntica (Unix-only) |
| [wterm](https://github.com/luinbytes/wterm) | Go | Terminal emulator com Bubble Tea |
| [conpty-go](https://github.com/qsocket/conpty-go) | Go | ConPTY implementation |

---

## Arquitetura: Clean Architecture

```
casca/
├── cmd/
│   └── casca/
│       └── main.go              # Entry point, daemon startup
├── internal/
│   ├── domain/                 # Core entities (no dependencies)
│   │   ├── session.go         # Session entity
│   │   ├── screen.go         # Screen capture entity
│   │   └── input.go          # Input entity
│   │
│   ├── usecase/              # Application logic
│   │   ├── spawn.go          # Spawn terminal session
│   │   ├── screenshot.go     # Capture screen (VT100 or image)
│   │   ├── sendkeys.go       # Send keys to session
│   │   ├── resize.go         # Resize terminal
│   │   ├── wait.go           # Wait for conditions
│   │   ├── kill.go           # Kill session
│   │   └── list.go           # List sessions
│   │
│   ├── adapter/              # External interfaces
│   │   ├── http/
│   │   │   ├── router.go     # HTTP route setup
│   │   │   └── handlers.go   # Request handlers
│   │   └── pipe/             # Named pipe (Windows)
│   │
│   └── infrastructure/       # Low-level implementations
│       ├── conpty/            # ConPTY implementation (qsocket/conpty-go)
│       ├── visible/           # Visible window implementation
│       ├── screen/           # Screenshot implementation
│       └── keys/              # Key sending implementation
│
└── pkg/
    └── vt100/                # VT100 parser
```

**Dependency Rule:** `domain` → `usecase` → `adapter` → `infrastructure`

---

## CASCA: 2 Modos de Operação

### Modo 1: ConPTY (Headless)
**Para:** cmd.exe, powershell, git, programas CLI simples

```
┌─────────────────────────────────────────────────┐
│              ConPTY Mode                        │
├─────────────────────────────────────────────────┤
│                                                  │
│  CASCA ──► ConPTY ──► cmd.exe                    │
│                    │                             │
│                    └── PTY (pseudo-terminal)    │
│                                                  │
│  Input:  CASCA write to PTY                     │
│  Output: PTY → VT100 parse → texto              │
│                                                  │
│  ✅ Rápido, invisível                           │
│  ⚠️  TUIs complexos podem não funcionar        │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Modo 2: Visible (Window)
**Para:** cmdit, vim, nano, htop, qualquer TUI que precise de janela real

```
┌─────────────────────────────────────────────────┐
│              Visible Mode                       │
├─────────────────────────────────────────────────┤
│                                                  │
│  CASCA ──► CreateProcess ──► cmd.exe /k cmdit   │
│                    │                             │
│                    └── Nova janela de terminal   │
│                                                  │
│  Screenshot: PrintWindow API                    │
│  Keys:      PostMessage / AttachThreadInput    │
│                                                  │
│  ✅ Funciona com QUALQUER TUI                  │
│  ⚠️  Mais lento, janela visível (pode minimizar) │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Auto-Detect Logic
```go
func SpawnWithFallback(command string, args []string, cols, rows int) (*Session, string, error) {
    // 1. Tenta ConPTY
    session, err := SpawnConPTY(command, args, cols, rows)
    if err != nil {
        return nil, "", err
    }

    // 2. Verifica se há output em 2 segundos
    if HasOutput(session, 2*time.Second) {
        return session, "conpty", nil
    }

    // 3. ConPTY não funcionou, mata e usa Visible
    session.Kill()

    // 4. Visible mode
    session, err = SpawnVisible(command, args)
    if err != nil {
        return nil, "", err
    }
    return session, "visible", nil
}
```

---

## API HTTP CASCA v3

### Endpoints

| Method | Path | Descrição |
|--------|------|-----------|
| POST | `/terminal/spawn` | Criar sessão |
| GET | `/terminal/list` | Listar sessões |
| GET | `/terminal/{id}` | Info da sessão |
| GET | `/terminal/{id}/screen` | Captura tela |
| POST | `/terminal/{id}/keys` | Enviar teclas |
| POST | `/terminal/{id}/resize` | Redimensionar |
| GET | `/terminal/{id}/wait` | Esperar condição |
| DELETE | `/terminal/{id}` | Encerrar |
| GET | `/health` | Health check |
| GET | `/metrics` | Métricas |

### Request/Response Examples

```json
// POST /terminal/spawn
Request: {
  "command": "cmdit.exe",
  "args": ["file.md"],
  "mode": "auto",
  "cols": 120,
  "rows": 40,
  "cwd": "C:\\projects"
}
Response: {
  "success": true,
  "session_id": "sess_abc123",
  "mode_used": "conpty",
  "pid": 12345
}

// POST /terminal/{id}/keys
Request: {
  "keys": "hello world\n",
  // ou estruturado:
  "keys": [{"type": "ctrl+c"}],
  "keys": [{"type": "alt"}, {"type": "f4"}]
}
Response: { "success": true }

// GET /terminal/{id}/screen?format=text
Response: {
  "type": "text",
  "content": "C:\\projects> dir\r\n Volume in drive C...\r\n",
  "hash": "sha256:abc123..."
}

// GET /terminal/{id}/screen?format=image
Response: {
  "type": "image",
  "path": "C:\\temp\\sess_abc_screen.png",
  "width": 1920,
  "height": 1080
}

// GET /terminal/{id}/wait?condition=text:Loading&timeout_ms=5000
// ou ?condition=stable:3s&timeout_ms=10000
Response: {
  "met": true,
  "waited_ms": 1200
}

// GET /terminal/list
Response: {
  "sessions": [
    {
      "id": "sess_abc123",
      "command": "cmdit.exe",
      "pid": 12345,
      "status": "running",
      "mode": "conpty",
      "cols": 120,
      "rows": 40,
      "created_at": "2026-05-01T10:00:00Z",
      "last_activity": "2026-05-01T10:00:05Z"
    }
  ]
}

// DELETE /terminal/{id}
Response: { "success": true }
```

---

## Fluxo de Interação

```
1. AIAgent ──► MCP terminal_spawn(command="cmdit")
                  │
                  ▼
2. MCP ──► HTTP POST /terminal/spawn
                  │
                  ▼
3. CASCA:
   - Tenta ConPTY primeiro
   - Se output em 2s, usa ConPTY
   - Se não, abre Visible window
                  │
                  ▼
4. CASCA retorna: session_id="abc", mode_used="conpty"
                  │
                  ▼
5. MCP ──► AIAgent: session_id="abc"

--- Get Screen ---
6. AIAgent ──► MCP terminal_get_screen(session_id="abc", format="text")
                  │
                  ▼
7. MCP ──► HTTP GET /terminal/abc/screen?format=text
                  │
                  ▼
8. CASCA:
   - ConPTY: Ler buffer, parse VT100, retornar texto
   - Visible: PrintWindow, salvar PNG, retornar path
                  │
                  ▼
9. MCP ──► AIAgent: texto ou path da imagem

--- Send Keys ---
10. AIAgent ──► MCP terminal_send_keys(session_id="abc", keys="Ctrl+S")
                  │
                  ▼
11. MCP ──► HTTP POST /terminal/abc/keys
                  │
                  ▼
12. CASCA:
    - ConPTY: write to PTY
    - Visible: PostMessage
                  │
                  ▼
13. MCP ──► AIAgent: success

--- Wait ---
14. AIAgent ──► MCP terminal_wait_for_stable(session_id="abc", timeout_ms=5000)
                  │
                  ▼
15. MCP ──► HTTP GET /terminal/abc/wait?condition=stable:2s&timeout_ms=5000
                  │
                  ▼
16. CASCA: Loop polling screen hash até estável ou timeout
                  │
                  ▼
17. MCP ──► AIAgent: {stable: true, waited_ms: 1500}

--- Kill ---
18. AIAgent ──► MCP terminal_kill(session_id="abc")
                  │
                  ▼
19. MCP ──► HTTP DELETE /terminal/abc
                  │
                  ▼
20. CASCA: Terminate process, cleanup session
```

---

## Key Sending: Hybrid Approach

### ConPTY Mode
```go
func (s *ConPTYSession) SendKeys(keys string) error {
    // Parsing simples
    for _, r := range keys {
        s.pty.Write([]byte{r})
    }
    return nil
}
```

### Visible Mode
```go
func (s *VisibleSession) SendKeys(keys string) error {
    // PostMessage para janela
    for _, r := range keys {
        user32.PostMessage(s.hwnd, user32.WM_CHAR, wparam(r), 0)
    }
    return nil
}
```

### Key Mapping Table
| Input | Output (bytes) |
|-------|----------------|
| `ctrl+c` | `0x03` (ETX) |
| `ctrl+d` | `0x04` (EOT) |
| `ctrl+z` | `0x1A` (SUB) |
| `enter` | `\r\n` (CRLF) |
| `escape` | `0x1B` (ESC) |
| `tab` | `\t` (TAB) |
| `arrow_up` | `\x1B[A` (VT100) |
| `arrow_down` | `\x1B[B` |

---

## Wait Conditions

### Tipos de Condição
1. **text:** Aguarda texto específico aparecer
2. **stable:** Aguarda tela estabilizar por X segundos

### Implementação
```go
func (s *Session) Wait(condition string, timeoutMs int) (bool, int, error) {
    start := time.Now()
    lastHash := ""

    for time.Since(start) < timeoutMs {
        screen := s.ReadOutput()
        hash := sha256(screen)

        if strings.HasPrefix(condition, "text:") {
            text := strings.TrimPrefix(condition, "text:")
            if strings.Contains(screen, text) {
                return true, int(time.Since(start).Milliseconds()), nil
            }
        } else if strings.HasPrefix(condition, "stable:") {
            duration, _ := time.ParseDuration(strings.TrimPrefix(condition, "stable:"))
            if hash == lastHash && lastHash != "" {
                if time.Since(stableSince) >= duration {
                    return true, int(time.Since(start).Milliseconds()), nil
                }
            } else {
                stableSince = time.Now()
            }
            lastHash = hash
        }

        time.Sleep(100 * time.Millisecond)
    }

    return false, int(time.Since(start).Milliseconds()), nil
}
```

---

## Stack Tecnológico

| Componente | Linguagem | Biblioteca | Motivo |
|-----------|-----------|------------|--------|
| CASCA Server | Go 1.21+ |stdlib `net/http` | HTTP server |
| ConPTY | Go | `github.com/qsocket/conpty-go` | ConPTY Windows |
| PTY | Go | `github.com/creack/pty` | Fallback PTY |
| Screenshot | Go | `github.com/gen2brain/mss` | Captura imagem |
| VT100 Parser | Go | custom (`pkg/vt100/`) | Parse texto |
| MCP Server | Python 3.11+ | `mcp` SDK | Padrão MCP |
| MCP Client | Python | `httpx` | HTTP client |

---

## Roadmap de Implementação

### Fase 1: CASCA Core (Go) — Sprint 1
**Meta:** Spawn e screen básicos funcionam

- [ ] `go mod init github.com/terminalvision/casca`
- [ ] Estrutura Clean Architecture
- [ ] Domain entities (Session, Screen, Input)
- [ ] HTTP server com net/http
- [ ] Session manager (in-memory map)
- [ ] Spawn com conpty-go
- [ ] VT100 parser (pkg/vt100)
- [ ] Screen capture (VT100 text)
- [ ] API endpoints (spawn, screen, kill, list)
- [ ] Teste: spawn cmd.exe, screen, kill

### Fase 2: CASCA Input + Resize — Sprint 2
**Meta:** Enviar teclas e redimensionar funciona

- [ ] Key parser (string → bytes)
- [ ] PTY write (ConPTY mode)
- [ ] Resize support
- [ ] Teste: echo hello, pipe input

### Fase 3: CASCA Wait Conditions — Sprint 3
**Meta:** Wait for text/stability funciona

- [ ] Wait for text
- [ ] Wait for stability (hash-based)
- [ ] Timeout handling
- [ ] Teste: vim, nano

### Fase 4: CASCA Visible Mode — Sprint 4
**Meta:** TUIs complexos (cmdit) funcionam

- [ ] FindWindow by PID
- [ ] PrintWindow screenshot
- [ ] PostMessage key sending
- [ ] Auto-detect mode (ConPTY fails → Visible)
- [ ] Teste: cmdit

### Fase 5: MCP Server — Sprint 5
**Meta:** MCP server conecta ao CASCA

- [ ] HTTP client em Python (httpx)
- [ ] MCP tools (spawn, screen, keys, resize, wait, kill, list)
- [ ] Error handling
- [ ] Timeout handling

### Fase 6: Integration — Sprint 6
**Meta:** Tudo funciona junto end-to-end

- [ ] Configuração (env vars, config file)
- [ ] Logging
- [ ] Error recovery
- [ ] Testes end-to-end com cmdit
- [ ] Documentação

---

## Riscos e Mitigações

| Risco | Prob | Impacto | Mitigação |
|-------|------|---------|-----------|
| conpty-go não funciona no Windows 11 | Baixa | Alto | creack/pty como fallback, Visible mode |
| Visible mode complexo (FindWindow, PostMessage) | Média | Alto | Começar com ConPTY, Visible só para cmdit |
| Screenshot é muito lento | Alta | Médio | Cache + diffonly + compressão |
| cmdit não funciona em nenhum modo | Alta | Alto | Testar cedo, buscar alternativas |
| Memory leak em long-running sessions | Média | Médio | Session timeout (30min idle) + cleanup |
| Go ConPTY bindings immaturos | Baixa | Alto | Testes extensivos, fallback Visible |

---

## IPC: HTTP + Named Pipe

### HTTP (Default)
```bash
# Desenvolvimento e debugging
casca --port 8787
curl http://localhost:8787/terminal/spawn -d '{"command": "cmd.exe"}'
```

### Named Pipe (Windows Production)
```go
// Windows: \\.\pipe\terminalvision
listener, _ := win.NewPipeListener("\\\\.\\pipe\\terminalvision")
conn, _ := listener.Accept()
// JSON-RPC over pipe
```

### Decision:
- **HTTP** para desenvolvimento/debugging
- **Named Pipe** como opção para produção Windows
- Não implementar Unix Socket (Windows-only por enquanto)

---

## Configuração

### Environment Variables
```bash
CASCA_PORT=8787                  # HTTP port (default: 8787)
CASCA_PIPE=\\.\pipe\terminalvision  # Named pipe path
CASCA_DEFAULT_SHELL=cmd.exe       # Shell padrão
CASCA_DEFAULT_COLS=120           # Colunas padrão
CASCA_DEFAULT_ROWS=40            # Linhas padrão
CASCA_SESSION_TIMEOUT=3600       # Timeout em segundos (default: 1h)
CASCA_LOG_LEVEL=info             # debug|info|warn|error
```

### Config File (YAML)
```yaml
# casca.yaml
server:
  port: 8787
  pipe: "\\.\pipe\terminalvision"

terminal:
  default_shell: "cmd.exe"
  default_cols: 120
  default_rows: 40

modes:
  conpty:
    timeout_ms: 2000  # Timeout para detectar se ConPTY funciona
  visible:
    start_minimized: true

session:
  max_idle_seconds: 3600
  cleanup_interval_seconds: 60
```

---

## Diff: v1 → v2 → v3

| Aspecto | v1 | v2 | v3 (Final) |
|---------|----|----|------------|
| Bibliotecas | Não especificadas | Mencionadas | **Identificadas: conpty-go, creack/pty, mss** |
| Arquitetura | Linear | Layers | **Clean Architecture com domínios** |
| Daemon | Não | Não | **Sim, long-running process** |
| IPC | HTTP | HTTP | **HTTP + Named Pipe fallback** |
| Modos | 1 | 2 | **2 + auto-detect** |
| Key sending | Básico | Básico | **Hybrid (PTY write + PostMessage)** |
| Wait conditions | Não | Básico | **Hash-based + pattern matching** |
| Visible mode | Mencionado | Detalhado | **PrintWindow + PostMessage + FindWindow** |
| Research | Não | Não | **Sim: agent-tui, wterm, conpty-go** |

---

## Conclusão

**Plano v3 inclui:**
1. ✅ Clean Architecture com camadas
2. ✅ Bibliotecas Go específicas identificadas
3. ✅ Daemon architecture
4. ✅ Wait conditions completas
5. ✅ Visible mode com PrintWindow/PostMessage detalhado
6. ✅ IPC com fallback Named Pipe
7. ✅ Key mapping detalhado
8. ✅ Auto-detect entre ConPTY e Visible
9. ✅ Research com projetos reais

**Pronto para implementação.**

---

## Próximos Passos

1. **Revisão:** Usuário analisa o plano
2. **Aprovação:** Usuário aprova ou solicita mudanças
3. **Sprint 1:** Implementar CASCA Core (Go)
4. **Iteração:** Feedback contínuo

---

**Versão:** 3.0
**Última atualização:** 2026-05-01
**Status:** Pronto para implementação
# TerminalVision: Arquitetura MCP + CASCA v2

> **Meta:** MCP Server que controla programas de terminal interativos (TUIs) como cmdit, vim, nano.
>
> **Problema Original:** subprocess.Popen cria pipes, não TTYs. TUIs detectam ausência de TTY e falham.
>
> **Solução:** CASCA é uma "casca" que cria terminais REAIS e permite captura de tela + envio de teclas.

---

## Conceito

```
┌──────────────────────────────────────────────────────────────────┐
│                      TerminalVision                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────┐        ┌─────────┐        ┌──────────────────┐   │
│   │   MCP   │◄──────►│  CASCA  │◄──────►│   Terminal(ões)   │   │
│   │(Python) │  HTTP  │  (Go)   │        │ cmd.exe, cmdit... │   │
│   │         │        │         │        │                  │   │
│   │ Tools:  │        │Modes:   │        │ 2 modos:         │   │
│   │ -spawn  │        │ -ConPTY │        │  -ConPTY (headless)│   │
│   │ -screen │        │ -Visible│        │  -Visible (window) │   │
│   │ -keys   │        │         │        │                  │   │
│   │ -resize │        │Screenshot│        │Screenshot:        │   │
│   │ -kill   │        │ -VT100  │        │ -VT100 (text)     │   │
│   │ -wait   │        │ -Image  │        │ -Image (capture)  │   │
│   └─────────┘        └─────────┘        └──────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Arquitetura Detalhada

### Componentes

#### CASCA (Go) — Terminal Manager
**Responsabilidade:** Criar terminais com TTY real, capturar tela, repassar teclas.

```
casca/
├── main.go                 # Entry point, HTTP server
├── terminal.go             # Gerencia processos de terminal
├── modes/
│   ├── conpty.go           # ConPTY mode (headless)
│   └── visible.go          # Visible window mode
├── screen/
│   ├── vt100.go            # Parser VT100 (texto)
│   └── capture.go          # Screenshot (imagem)
├── keys/
│   └── send.go            # Envio de teclas
└── api/
    ├── router.go           # HTTP routes
    └── handlers.go         # Request/response handlers
```

**CASCA tem 2 modos operacionais:**

| Modo | Quando usar | Screenshot | Velocidade | TTY |
|------|-------------|------------|------------|-----|
| **ConPTY** | Programas texto simples | Parser VT100 | Rápido | Sim |
| **Visible** | TUIs complexos (cmdit, vim) | Captura real | Lento | Sim |

**Decisão de modo:**
- CASCA tenta ConPTY primeiro
- Se output em 2s não chegar, sugere Visible mode
- Ou modo explícito via parâmetro `mode: "conpty"|"visible"|"auto"`

#### MCP (Python) — MCP Server
**Responsabilidade:** Servidor MCP + cliente HTTP para CASCA.

```
mcp/
├── main.py                 # Entry point MCP
├── client/
│   └── casca_client.py     # HTTP client para CASCA
├── tools/
│   ├── terminal_spawn.py
│   ├── terminal_get_screen.py
│   ├── terminal_send_keys.py
│   ├── terminal_resize.py
│   ├── terminal_wait_for_stable.py
│   ├── terminal_list_sessions.py
│   └── terminal_kill.py
├── types/
│   └── types.py            # Pydantic models
├── pyproject.toml
└── requirements.txt
```

---

## API CASCA v2

### Endpoints

```
POST   /terminal/spawn          # Criar nova sessão
GET    /terminal/list          # Listar sessões
GET    /terminal/{id}/screen   # Capturar tela
POST   /terminal/{id}/keys     # Enviar teclas
POST   /terminal/{id}/resize   # Redimensionar
GET    /terminal/{id}/wait     # Espera tela estabilizar
DELETE /terminal/{id}          # Encerrar sessão
GET    /health                 # Health check
```

### Request/Response Examples

```json
// POST /terminal/spawn
Request: {
  "command": "cmdit.exe",
  "args": ["file.md"],
  "mode": "auto",        // "conpty", "visible", "auto"
  "cols": 120,
  "rows": 40,
  "cwd": "C:\\projects"
}
Response: {
  "success": true,
  "session_id": "sess_abc123",
  "mode_used": "conpty",  // ou "visible"
  "pid": 12345
}

// POST /terminal/{id}/keys
Request: {
  "keys": "hello world\n"                    // literal
  // ou
  "keys": [{"type": "ctrl"}, {"type": "key", "key": "s"}]  // estruturado
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

// GET /terminal/{id}/wait?timeout_ms=5000
Response: {
  "stable": true,
  "hash": "sha256:abc123...",
  "waited_ms": 1200
}

// DELETE /terminal/{id}
Response: { "success": true }
```

---

## Fluxo de Interação

```
1. AIAgent → MCP terminal_spawn(command="cmdit")
                 ↓
2. MCP → HTTP POST /terminal/spawn
                 ↓
3. CASCA:
   - Tenta ConPTY primeiro
   - Se output em 2s, usa ConPTY
   - Se não, abre Visible window
                 ↓
4. CASCA retorna: session_id="abc", mode_used="conpty"
                 ↓
5. MCP → AIAgent: session_id="abc"

--- Get Screen ---
6. AIAgent → MCP terminal_get_screen(session_id="abc", format="text")
                 ↓
7. MCP → HTTP GET /terminal/abc/screen?format=text
                 ↓
8. CASCA retorna conteúdo da tela
                 ↓
9. MCP → AIAgent: texto da tela

--- Send Keys ---
10. AIAgent → MCP terminal_send_keys(session_id="abc", keys="Ctrl+S")
                 ↓
11. MCP → HTTP POST /terminal/abc/keys
                 ↓
12. CASCA repassa para stdin do processo

--- Kill ---
13. AIAgent → MCP terminal_kill(session_id="abc")
                 ↓
14. MCP → HTTP DELETE /terminal/abc
                 ↓
15. CASCA mata processo, limpa sessão
```

---

## Decisões Técnicas

### Por que Go para CASCA?

| Razão | Explicação |
|-------|------------|
| **go-pty** | Bindings ConPTY maduros e testados |
| **Binário único** | Não precisa runtime Python |
| **Cross-compile** | Windows, Linux, Mac de uma compilação |
| **Goroutines** | Múltiplas sessões em paralelo |
| **Screenshot libs** | Bindings para captura nativa disponíveis |

### Por que 2 modos (ConPTY + Visible)?

**ConPTY (headless):**
- Para: cmd.exe, powershell, programas CLI
- Vantagem: Rápido, invisível
- Desvantagem: TUIs complexos podem não funcionar

**Visible (window):**
- Para: cmdit, vim, nano, htop, qualquer TUI
- Vantagem: Funciona com qualquer programa
- Desvantagem: Mais lento, janela visível

**Fallback automático:**
```go
func spawnWithFallback(command string) (*Session, string) {
    // Tenta ConPTY primeiro
    session, err := spawnConPTY(command)
    if err == nil {
        // Verifica se há output em 2 segundos
        if hasOutput(session, 2*time.Second) {
            return session, "conpty"
        }
        // ConPTY não funcionou, mata e usa Visible
        session.Kill()
    }
    // Visible mode
    return spawnVisible(command), "visible"
}
```

### Por que screenshot é central?

**TUIs complexos (cmdit, vim):**
- Usam renderização customizada (Bubble Tea, ncurses)
- Parser VT100 não funciona
- Screenshot real é a única opção

**TUIs simples:**
- Parser VT100 é mais leve
- Retorna texto editável
- Screenshot como fallback

---

## Stack Tecnológico

| Componente | Linguagem | Biblioteca | Motivo |
|-----------|-----------|------------|--------|
| MCP Server | Python 3.11+ | `mcp` SDK | Padrão MCP |
| CASCA | Go 1.21+ | go-pty, net/http | Binário único, ConPTY |
| Terminal (headless) | Sistema | ConPTY | TTY real no Windows |
| Terminal (visible) | Sistema | Windows API | Janela real |
| Screenshot texto | Go | vt100 parser | Leve |
| Screenshot imagem | Go | github.com/gen2brain/msh | Cross-platform |

---

## Roadmap de Implementação

### Fase 1: CASCA Minimal (Go)
- [x] Estrutura de pastas
- [ ] HTTP server com gorilla/mux
- [ ] Spawn subprocess básico
- [ ] Captura stdout
- [ ] CRUD de sessões

### Fase 2: CASCA + ConPTY (Go)
- [ ] go-pty para ConPTY
- [ ] Parser VT100
- [ ] Resize
- [ ] Session state

### Fase 3: CASCA + Visible Mode (Go)
- [ ] Criar janela visível
- [ ] Screenshot da janela
- [ ] Enviar teclas (PostMessage)
- [ ] Focus management

### Fase 4: MCP Server (Python)
- [ ] Cliente HTTP para CASCA
- [ ] Tools MCP básicas
- [ ] wait_for_stable helper
- [ ] list_vision_mcps discovery

### Fase 5: Integração e Testes
- [ ] Testar com cmd.exe
- [ ] Testar com cmdit
- [ ] Testar com vim/nano
- [ ] Error handling
- [ ] Logging

---

## Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|-------|--------------|-----------|
| ConPTY API complexa no Windows | Média | go-pty abstrai, Visible como fallback |
| Visible mode precisa de janela | Baixa | Janela pode ser minimizada |
| Screenshot é muito lento | Alta | Diffonly + cache + compressão |
| Memory leak em long-running | Média | Session timeout + cleanup automático |
| cmdit não funciona em ConPTY | Alta | Visible mode obrigatório para cmdit |
| CASCA crash mata todas sessões | Baixa | Persistência de estado em arquivo |

---

## Configuração

```yaml
# casca.yaml
server:
  host: "localhost"
  port: 8787
  pipe: "\\\\.\\pipe\\terminalvision"  # Named pipe (futuro)

terminal:
  default_shell: "cmd.exe"
  default_cols: 120
  default_rows: 40

modes:
  conpty:
    timeout_ms: 2000  # Timeout para detectar se ConPTY funciona
  visible:
    start_minimized: true  # Visible mas não打扰
    screenshot_interval_ms: 100

session:
  max_idle_seconds: 3600  # Cleanup de sessões órfãs
  persist_to_file: false
```

---

## Testes

### CASCA tests (Go)
```bash
go test ./... -v
```

### MCP tests (Python)
```bash
pytest tests/ -v
```

### Integration tests
```bash
# 1. Build CASCA
cd casca && go build -o casca.exe .

# 2. Start CASCA
./casca.exe --port 8787

# 3. Test spawn
curl -X POST http://localhost:8787/terminal/spawn \
  -H "Content-Type: application/json" \
  -d '{"command": "cmd.exe /c echo hello"}'

# 4. Test screen
curl http://localhost:8787/terminal/sess_abc/screen

# 5. Test kill
curl -X DELETE http://localhost:8787/terminal/sess_abc
```

---

## Perguntas em Aberto

1. **Visible mode é aceitável?** (janela visível do programa)
2. **Qual o ambiente final?** (Windows only? Cross-platform?)
3. **cmdit funciona em ConPTY?** (precisamos testar primeiro)
4. **CASCA como serviço permanente ou start/stop?**
5. **Persistência de sessões?** (memória vs arquivo vs SQLite)

---

## Diff: Original vs Novo Plano

| Aspecto | Original | Novo |
|---------|----------|------|
| TTY handling | winpty (imperfeito) | ConPTY + Visible fallback |
| Screenshot | Parser VT100 apenas | Parser VT100 + Image |
| Modos | 1 | 2 (headless + visible) |
| Error handling | Timeout only | Fallback automático |
| CASCA | subprocess wrapper | Terminal manager completo |
| cmdit | Não mencionado | Modo Visible obrigatório |
| Go libs | Não especificadas | go-pty explicitado |

---

**Versão:** 2.0
**Data:** 2026-05-01
**Status:** Para revisão
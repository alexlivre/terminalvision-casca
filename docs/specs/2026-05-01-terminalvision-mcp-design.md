# TerminalVision-MCP — Design Document

> **Status:** Design completo aprovado
> **Data:** 2026-05-01
> **Versão:** 1.0

---

## 1. Visão Geral do Projeto

**Nome:** TerminalVision-MCP

**Objetivo:** Criar um MCP Server universal que dá aos agentes de IA visão e controle humano do terminal, funcionando com modelos que não têm visão nativa (como DeepSeek e MiniMax M2.7).

**Plataforma:** Cross-platform (Windows 11 priority, Linux, Mac)
**Stack:** Python 3.11+
**Cliente primário:** Qwen Code (com compatibilidade geral para todos)

---

## 2. Arquitetura Geral

```
┌─────────────────────────────────────────────────────────┐
│                     MCP Server                          │
│                   (Python asyncio)                      │
├─────────────────────────────────────────────────────────┤
│  Tools Layer (MCP exposed)                              │
│  ┌──────────┬──────────┬──────────┬──────────┬─────────┐  │
│  │spawn    │get_screen│send_keys│wait_stable│list    │  │
│  └────┬─────┴────┬─────┴────┬─────┴────┬──────┴────┬────┘  │
├─────────────────────────────────────────────────────────┤
│  Session Manager (in-memory, TTL 30min)                 │
│  ┌──────────┬──────────┬──────────┬──────────┐          │
│  │session_1 │session_2 │session_3 │  ...    │          │
│  └────┬─────┴────┬─────┴────┬─────┴─────────┘          │
├─────────────────────────────────────────────────────────┤
│  PTY Handler (platform-specific)                        │
│  ┌─────────────┬─────────────────┬─────────────────┐    │
│  │  Linux/macOS│  Windows (ConPTY)│                 │    │
│  │    pty     │                 │                 │    │
│  └─────────────┴─────────────────┴─────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  Capture Engine                                         │
│  ┌─────────────┬─────────────────┬─────────────────┐    │
│  │  Text (VT100│  Image (mss+PIL)│  Stability      │    │
│  │  + pyte)    │                 │  Detection      │    │
│  └─────────────┴─────────────────┴─────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  Vision Discovery                                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Scan Qwen/Claude configs → List available     │    │
│  │  vision MCPs → Auto-select or let agent choose   │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Stack Tecnológico

| Componente | Tech | Rationale |
|-----------|------|-----------|
| Language | Python 3.11+ | Robustez, asyncio nativo, cross-platform |
| MCP SDK | `mcp` (oficial) | Padrão oficial para MCP servers |
| PTY handling | `pty` (Unix), `pywin32+ConPTY` (Win) | Nativo, sem deps extras |
| Terminal parsing | `pyte` | Parser VT100/ANSI completo, leve |
| Screenshot (Win) | `mss` + PIL | Captura rápida de janelas |
| Screenshot (Unix) | `mss` | Cross-platform, confiável |
| Key handling | `pexpect` patterns | Mapear sequências de teclas complexas |

---

## 4. Ferramentas MCP (API pública)

### terminal_spawn
```python
terminal_spawn(command: str, cwd: str?, cols: int = 120, rows: int = 40)
```
- Creates a new terminal session with specified command
- Returns `session_id: str`
- Shell default: bash (Unix), cmd.exe (Windows)

### terminal_get_screen
```python
terminal_get_screen(session_id: str, format: "text" | "image")
```
- **format="text"**: Returns full visible buffer via PTY + VT100 parsing
  - Returns `{"type": "text", "content": str, "hash": str}`
- **format="image"**: Captures real screenshot
  - Returns `{"type": "image", "path": str}`

### terminal_send_keys
```python
terminal_send_keys(session_id: str, keys: str)
```
- Sends key sequences supporting: `Ctrl+P`, `Esc`, arrow keys, complex sequences
- Returns `{"success": bool}`

### terminal_wait_for_stable
```python
terminal_wait_for_stable(session_id: str, timeout_ms: int = 5000)
```
- Waits for screen to stop changing (stable frames)
- Returns `{"stable": bool, "final_hash": str}`

### terminal_list_sessions
```python
terminal_list_sessions()
```
- Lists all active sessions
- Returns `[{"id": str, "command": str, "created": timestamp}]`

### terminal_resize
```python
terminal_resize(session_id: str, cols: int, rows: int)
```
- Resizes terminal window
- Returns `{"success": bool}`

### terminal_kill
```python
terminal_kill(session_id: str)
```
- Terminates a session
- Returns `{"success": bool}`

### list_vision_mcps (bonus - internal discovery)
```python
list_vision_mcps()
```
- Lists available vision MCPs discovered from configs
- Returns `[{"name": str, "description": str}]`

---

## 5. Descoberta de MCPs de Visão

### Fluxo de Descoberta

1. **Ao iniciar:** Escaneia configs de clientes MCP conhecidos
2. **Qwen Code:** `%USERPROFILE%\.qwen\settings.json` (Win) / `~/.qwen/settings.json` (Unix)
3. **Claude Code:** `%USERPROFILE%\.claude\settings.json`
4. **Extrai:** Lista de tools de cada MCP configurado
5. **Filtra:** MCPs com tools de visão (describe image, analyze, etc.)
6. **Expõe:** Via tool `list_vision_mcps`

### Fallback
- `TERMINALVISION_VISION_MCP_LIST` env var (separado por vírgulas)
- Manual registration via `register_vision_mcp` tool

### Regras
- **Não hardcodar** nenhum MCP específico (ex: não mencionar Gemma ou MiniMax)
- **Descobrir automaticamente** todos os MCPs de visão configurados
- Se múltiplos disponíveis: perguntar ao agente/usuário qual usar

---

## 6. Comportamento Inteligente

### Decisão Texto vs Imagem

```
┌─────────────────────────────────────────────┐
│  Agent requests screen capture              │
└─────────────────┬───────────────────────────┘
                  ▼
         ┌────────────────┐
         │ Is detailed    │──No──► Use TEXT (fast, efficient)
         │ vision needed? │
         └───────┬────────┘
                 │Yes
         ┌───────▼────────┐
         │ Capture IMAGE  │
         └───────┬────────┘
                 ▼
         ┌────────────────────────────┐
         │ Does model support image?  │
         └───────┬────────┬───────────┘
                 │Yes     │No
                 ▼        ▼
         ┌───────────┐  ┌─────────────────────┐
         │ Send img  │  │ Discover vision MCP │
         │ to model  │  │ Call it to describe │
         └───────────┘  └─────────────────────┘
```

### Regra Principal
- **Sempre que possível:** Usar texto (mais rápido, mais eficiente)
- **Quando necessário:** Usar imagem + chamar MCP de descrição de imagens

---

## 7. Estrutura de Diretórios

```
terminalvision-mcp/
├── terminalvision_mcp/
│   ├── __init__.py
│   ├── main.py              # Entry point, MCP server
│   ├── types.py             # Type definitions (Pydantic)
│   ├── session_manager.py   # Session lifecycle + TTL cleanup
│   ├── pty_handler.py       # Platform-specific PTY (Unix/Win)
│   ├── capture.py           # Text (pyte) + image (mss) capture
│   ├── stability.py         # Frame comparison + stable detection
│   ├── key_mapper.py        # Key sequence mapping (Ctrl+C, arrows, etc.)
│   └── vision_discovery.py  # Find vision MCPs in client configs
├── tests/
│   ├── test_session_manager.py
│   ├── test_capture.py
│   ├── test_stability.py
│   └── test_key_mapper.py
├── examples/
│   └── usage_demo.py
├── docs/
│   └── specs/
│       └── 2026-05-01-terminalvision-mcp-design.md
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 8. Decisões de Design

| Decisão | Escolha | Rationale |
|---------|---------|-----------|
| Plataforma | Win11 + Linux priority, Mac secondary | Windows como primeiro uso |
| Captura primária | Texto via PTY + pyte | Mais rápido, eficiente |
| Captura secundária | Imagem via mss + PIL | Para casos com detalhes visuais |
| Persistence | In-memory + TTL 30min | Simples, atende use case |
| Descoberta de visão | Ler configs dos clientes | Transparente, já configurado |
| Shell default | bash (Unix), cmd.exe (Win) | Universal e robusto |
| Stability detection | Hash comparison of frames | Simples e eficaz |

---

## 9. Requisitos Técnicos

- [x] Funcionar com qualquer TUI (editor custom, Vim, htop, etc.)
- [x] Suporte a múltiplas sessões persistentes
- [x] Robustez alta (redraws, alternate screen, Unicode, etc.)
- [x] Fácil de adicionar em Qwen Code, Claude Code, etc.
- [x] Priorizar captura em texto (mais rápido e eficiente)
- [x] Oferecer captura como imagem quando necessário
- [x] Descobrir automaticamente MCPs de visão disponíveis

---

## 10. Shell Defaults por Plataforma

| OS | Default | Fallback |
|---|---|---|
| Linux | `bash` (ou `$SHELL`) | `/bin/sh` |
| macOS | `zsh` (Catalina+) | `bash` |
| Windows | `cmd.exe` | `powershell.exe` |

Detecção automática via variáveis de ambiente.

---

## 11. TTL e Cleanup de Sessões

- **TTL padrão:** 30 minutos após última atividade
- **Cleanup:** Background task remove sessões expired
- **Orphan cleanup:** Se cliente disconnect sem chamar `kill`, sessão fica disponível até TTL
- **Max sessions:** 50 sessões simultâneas (configurável)

---

## 12. Segurança e Robustez

- **Isolamento:** Cada sessão é processo separado
- **Timeout:** Comandos podem ter timeout individual
- **Input sanitization:** Keys mapeadas e validadas antes de enviar
- **Unicode support:** UTF-8 completo
- **Alternate screen:** Suporte a programas que usam alternate buffer (Vim, less, etc.)

---

## 13. Próximos Passos (Implementação)

1. Criar estrutura de diretórios
2. Setup `pyproject.toml` e `requirements.txt`
3. Implementar `types.py` (Pydantic models)
4. Implementar `pty_handler.py` (platform-specific PTY)
5. Implementar `session_manager.py` (sessões + TTL)
6. Implementar `capture.py` (texto + imagem)
7. Implementar `stability.py` (detecção de estabilidade)
8. Implementar `key_mapper.py` (sequências de teclas)
9. Implementar `vision_discovery.py` (descobrir MCPs de visão)
10. Implementar `main.py` (servidor MCP)
11. Criar README.md
12. Testar e validar

---

**Documento criado:** 2026-05-01
**Status:** Pronto para implementação

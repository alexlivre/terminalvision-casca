package usecase

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"time"

	"github.com/alexlivre/terminalvision-casca/internal/domain"
	"github.com/alexlivre/terminalvision-casca/internal/infrastructure"
)

type SessionManager struct {
	ptySessions map[string]*domain.Session
	ptyManager  *infrastructure.PTYManager
}

func NewSessionManager() *SessionManager {
	return &SessionManager{
		ptySessions: make(map[string]*domain.Session),
		ptyManager:  infrastructure.NewPTYManager(),
	}
}

func generateID() string {
	b := make([]byte, 8)
	rand.Read(b)
	return "sess_" + hex.EncodeToString(b)
}

func (m *SessionManager) Spawn(req domain.SpawnRequest) (*domain.SpawnResponse, error) {
	if req.Command == "" {
		req.Command = "cmd.exe"
	}
	if req.Cols <= 0 {
		req.Cols = 120
	}
	if req.Rows <= 0 {
		req.Rows = 40
	}

	sessionID := generateID()
	ptySession, err := m.ptyManager.Spawn(sessionID, req.Command, req.Args, req.Cols, req.Rows)
	if err != nil {
		return &domain.SpawnResponse{Success: false, Error: err.Error()}, err
	}

	session := domain.NewSession(sessionID, req.Command, req.Args, ptySession.PID(), domain.ModeConPTY, req.Cols, req.Rows)
	m.ptySessions[sessionID] = session

	return &domain.SpawnResponse{
		Success:   true,
		SessionID: sessionID,
		ModeUsed:  string(domain.ModeConPTY),
		PID:       ptySession.PID(),
		Command:   req.Command,
	}, nil
}

func (m *SessionManager) GetScreen(sessionID string, format string) (*domain.ScreenResponse, error) {
	session, ok := m.ptySessions[sessionID]
	if !ok {
		return nil, errors.New("session not found")
	}
	ptySession, ok := m.ptyManager.Get(sessionID)
	if !ok {
		return nil, errors.New("pty session not found")
	}

	var content string
	for {
		data, err := ptySession.ReadOutput()
		if err != nil || len(data) == 0 {
			break
		}
		session.AppendBuffer(data)
		content += string(data)
	}
	if content == "" {
		content = session.ReadBuffer()
	}

	return &domain.ScreenResponse{Type: "text", Content: content}, nil
}

func (m *SessionManager) SendKeys(sessionID string, req domain.KeysRequest) (*domain.KeysResponse, error) {
	ptySession, ok := m.ptyManager.Get(sessionID)
	if !ok {
		return &domain.KeysResponse{Success: false, Error: "session not found"}, errors.New("session not found")
	}
	keys, err := ParseKeys(req.Keys)
	if err != nil {
		return &domain.KeysResponse{Success: false, Error: err.Error()}, err
	}
	err = ptySession.WriteInput(keys)
	if err != nil {
		return &domain.KeysResponse{Success: false, Error: err.Error()}, err
	}
	return &domain.KeysResponse{Success: true}, nil
}

func (m *SessionManager) Resize(sessionID string, cols, rows int) (*domain.ResizeResponse, error) {
	ptySession, ok := m.ptyManager.Get(sessionID)
	if !ok {
		return &domain.ResizeResponse{Success: false, Error: "session not found"}, errors.New("session not found")
	}
	err := ptySession.Resize(cols, rows)
	if err != nil {
		return &domain.ResizeResponse{Success: false, Error: err.Error()}, err
	}
	if session, ok := m.ptySessions[sessionID]; ok {
		session.Cols = cols
		session.Rows = rows
	}
	return &domain.ResizeResponse{Success: true}, nil
}

func (m *SessionManager) Wait(sessionID string, req domain.WaitRequest) (*domain.WaitResponse, error) {
	ptySession, ok := m.ptyManager.Get(sessionID)
	if !ok {
		return nil, errors.New("session not found")
	}
	start := time.Now()
	timeout := time.Duration(req.TimeoutMs) * time.Millisecond
	deadline := start.Add(timeout)

	for time.Now().Before(deadline) {
		var content string
		for {
			data, err := ptySession.ReadOutput()
			if err != nil || len(data) == 0 {
				break
			}
			content += string(data)
		}
		if len(content) > 0 && len(req.Condition) > 5 && req.Condition[:5] == "text:" {
			text := req.Condition[5:]
			if contains(content, text) {
				return &domain.WaitResponse{Met: true, WaitedMs: int(time.Since(start).Milliseconds())}, nil
			}
		}
		time.Sleep(100 * time.Millisecond)
	}
	return &domain.WaitResponse{Met: false, WaitedMs: int(time.Since(start).Milliseconds())}, nil
}

func (m *SessionManager) List() *domain.ListResponse {
	sessions := make([]map[string]interface{}, 0)
	for id, session := range m.ptySessions {
		running := m.ptyManager.IsRunning(id)
		status := domain.StatusRunning
		if !running {
			status = domain.StatusExited
		}
		sessions = append(sessions, map[string]interface{}{
			"session_id": session.ID,
			"command":    session.Command,
			"pid":        session.PID,
			"mode":       session.Mode,
			"cols":       session.Cols,
			"rows":       session.Rows,
			"status":     status,
			"created_at": session.CreatedAt.Format(time.RFC3339),
		})
	}
	return &domain.ListResponse{Sessions: sessions}
}

func (m *SessionManager) Kill(sessionID string) (*domain.KillResponse, error) {
	if _, ok := m.ptySessions[sessionID]; !ok {
		return &domain.KillResponse{Success: false, Error: "session not found"}, errors.New("session not found")
	}
	m.ptyManager.Remove(sessionID)
	delete(m.ptySessions, sessionID)
	return &domain.KillResponse{Success: true}, nil
}

func contains(s, substr string) bool {
	if len(s) < len(substr) {
		return false
	}
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
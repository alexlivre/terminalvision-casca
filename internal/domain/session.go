package domain

import (
	"sync"
	"time"
)

// Mode represents the terminal mode
type Mode string

const (
	ModeConPTY  Mode = "conpty"
	ModeVisible Mode = "visible"
)

// Session represents a terminal session
type Session struct {
	ID        string
	Command   string
	Args      []string
	PID       int
	Mode      Mode
	Cols      int
	Rows      int
	CreatedAt time.Time
	Status    SessionStatus
	Buffer    *ScreenBuffer

	mu     sync.RWMutex
}

// ScreenBuffer holds terminal output
type ScreenBuffer struct {
	content []byte
	mu      sync.RWMutex
}

// SessionStatus represents session state
type SessionStatus string

const (
	StatusRunning  SessionStatus = "running"
	StatusExited   SessionStatus = "exited"
	StatusUnknown SessionStatus = "unknown"
)

// NewSession creates a new session
func NewSession(id, command string, args []string, pid int, mode Mode, cols, rows int) *Session {
	return &Session{
		ID:        id,
		Command:   command,
		Args:      args,
		PID:       pid,
		Mode:      mode,
		Cols:      cols,
		Rows:      rows,
		CreatedAt: time.Now(),
		Status:    StatusRunning,
		Buffer:    &ScreenBuffer{},
	}
}

// ReadBuffer returns current screen content
func (s *Session) ReadBuffer() string {
	s.Buffer.mu.RLock()
	defer s.Buffer.mu.RUnlock()
	return string(s.Buffer.content)
}

// AppendBuffer appends content to screen buffer
func (s *Session) AppendBuffer(data []byte) {
	s.Buffer.mu.Lock()
	s.Buffer.content = append(s.Buffer.content, data...)
	s.Buffer.mu.Unlock()
}

// ClearBuffer clears the screen buffer
func (s *Session) ClearBuffer() {
	s.Buffer.mu.Lock()
	s.Buffer.content = nil
	s.Buffer.mu.Unlock()
}

// IsRunning checks if session is still running
func (s *Session) IsRunning() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.Status == StatusRunning
}

// SetExited marks session as exited
func (s *Session) SetExited() {
	s.mu.Lock()
	s.Status = StatusExited
	s.mu.Unlock()
}

// Info returns session info for API response
func (s *Session) Info() map[string]interface{} {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return map[string]interface{}{
		"session_id":    s.ID,
		"command":       s.Command,
		"args":          s.Args,
		"pid":           s.PID,
		"mode":          s.Mode,
		"cols":          s.Cols,
		"rows":          s.Rows,
		"status":        s.Status,
		"created_at":    s.CreatedAt.Format(time.RFC3339),
	}
}

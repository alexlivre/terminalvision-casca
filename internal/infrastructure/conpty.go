package infrastructure

import (
	"fmt"
	"io"
	"os"
	"os/exec"
	"sync"
	"time"

	"github.com/creack/pty"
)

type PTYSession struct {
	id      string
	pid     int
	command string
	args    []string
	cols    int
	rows    int
	ptmx    *os.File
	cmd     *exec.Cmd
	closed  bool
	closeMu sync.RWMutex
}

func NewPTYSession(id, command string, args []string, cols, rows int) (*PTYSession, error) {
	cmd := exec.Command(command, args...)
	ptmx, err := pty.Start(cmd)
	if err != nil {
		return nil, fmt.Errorf("failed to start PTY: %w", err)
	}

	return &PTYSession{
		id:      id,
		pid:     cmd.Process.Pid,
		command: command,
		args:    args,
		cols:    cols,
		rows:    rows,
		ptmx:    ptmx,
		cmd:     cmd,
	}, nil
}

func (s *PTYSession) PID() int {
	return s.pid
}

func (s *PTYSession) ReadOutput() ([]byte, error) {
	s.closeMu.RLock()
	defer s.closeMu.RUnlock()
	if s.closed || s.ptmx == nil {
		return nil, nil
	}
	buf := make([]byte, 4096)
	s.ptmx.SetReadDeadline(time.Now().Add(100 * time.Millisecond))
	n, err := s.ptmx.Read(buf)
	if err != nil && err != io.EOF {
		if n == 0 {
			return nil, nil
		}
	}
	return buf[:n], nil
}

func (s *PTYSession) WriteInput(data []byte) error {
	s.closeMu.RLock()
	defer s.closeMu.RUnlock()
	if s.closed || s.ptmx == nil {
		return fmt.Errorf("session closed")
	}
	_, err := s.ptmx.Write(data)
	return err
}

func (s *PTYSession) Resize(cols, rows int) error {
	s.closeMu.RLock()
	defer s.closeMu.RUnlock()
	if s.closed {
		return fmt.Errorf("session closed")
	}
	s.cols = cols
	s.rows = rows
	pty.Setsize(s.ptmx, &pty.Winsize{Cols: uint16(cols), Rows: uint16(rows)})
	return nil
}

func (s *PTYSession) Close() error {
	s.closeMu.Lock()
	defer s.closeMu.Unlock()
	if s.closed {
		return nil
	}
	s.closed = true
	if s.ptmx != nil {
		s.ptmx.Close()
	}
	if s.cmd != nil && s.cmd.Process != nil {
		s.cmd.Process.Kill()
	}
	return nil
}

type PTYManager struct {
	sessions map[string]*PTYSession
	mu       sync.RWMutex
}

func NewPTYManager() *PTYManager {
	return &PTYManager{
		sessions: make(map[string]*PTYSession),
	}
}

func (m *PTYManager) Spawn(id, command string, args []string, cols, rows int) (*PTYSession, error) {
	session, err := NewPTYSession(id, command, args, cols, rows)
	if err != nil {
		return nil, err
	}
	pty.Setsize(session.ptmx, &pty.Winsize{Cols: uint16(cols), Rows: uint16(rows)})
	session.WriteInput([]byte("set TERM=xterm-256color\n"))

	m.mu.Lock()
	m.sessions[id] = session
	m.mu.Unlock()
	return session, nil
}

func (m *PTYManager) Get(id string) (*PTYSession, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	session, ok := m.sessions[id]
	return session, ok
}

func (m *PTYManager) Remove(id string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	if session, ok := m.sessions[id]; ok {
		session.Close()
		delete(m.sessions, id)
	}
	return nil
}

func (m *PTYManager) HasOutput(session *PTYSession, timeout time.Duration) bool {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		output, _ := session.ReadOutput()
		if len(output) > 0 {
			return true
		}
		time.Sleep(100 * time.Millisecond)
	}
	return false
}

func (m *PTYManager) IsRunning(id string) bool {
	m.mu.RLock()
	session, ok := m.sessions[id]
	m.mu.RUnlock()
	if !ok {
		return false
	}
	if session.cmd == nil || session.cmd.Process == nil {
		return false
	}
	err := session.cmd.Process.Signal(nil)
	return err == nil
}

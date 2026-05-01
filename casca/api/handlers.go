package api

import (
	"encoding/json"
	"log"
	"net/http"
	"os/exec"
	"sync"

	"github.com/gorilla/mux"
)

// Session represents a terminal session
type Session struct {
	ID      string
	Command string
	Pid     int
	Process *exec.Cmd
	Buffer  []byte
	Mu      sync.Mutex
}

// SessionStore manages all sessions
type SessionStore struct {
	sessions map[string]*Session
	mu       sync.RWMutex
}

var store = &SessionStore{
	sessions: make(map[string]*Session),
}

func handleSpawn(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Command string `json:"command"`
		Cwd     string `json:"cwd"`
		Cols    int    `json:"cols"`
		Rows    int    `json:"rows"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	if req.Command == "" {
		req.Command = "cmd.exe"
	}

	// Create session ID
	sessionID := generateID()

	// Start the process
	cmd := exec.Command("cmd.exe", "/c", req.Command)
	if req.Cwd != "" {
		cmd.Dir = req.Cwd
	}

	cmd.Stdout = nil // Will capture via pipe
	cmd.Stderr = nil

	if err := cmd.Start(); err != nil {
		json.NewEncoder(w).Encode(map[string]interface{}{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	session := &Session{
		ID:      sessionID,
		Command: req.Command,
		Pid:     cmd.Process.Pid,
		Process: cmd,
	}

	store.mu.Lock()
	store.sessions[sessionID] = session
	store.mu.Unlock()

	log.Printf("Session %s created for command: %s (PID: %d)", sessionID, req.Command, cmd.Process.Pid)

	json.NewEncoder(w).Encode(map[string]interface{}{
		"success":     true,
		"session_id":  sessionID,
		"pid":         cmd.Process.Pid,
		"command":     req.Command,
	})
}

func handleList(w http.ResponseWriter, r *http.Request) {
	store.mu.RLock()
	defer store.mu.RUnlock()

	sessions := make([]map[string]interface{}, 0)
	for id, s := range store.sessions {
		sessions = append(sessions, map[string]interface{}{
			"session_id": id,
			"command":    s.Command,
			"pid":        s.Pid,
			"status":     "running",
		})
	}

	json.NewEncoder(w).Encode(map[string]interface{}{
		"sessions": sessions,
	})
}

func handleSend(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["id"]

	var req struct {
		Keys string `json:"keys"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	store.mu.RLock()
	session, ok := store.sessions[sessionID]
	store.mu.RUnlock()

	if !ok {
		http.Error(w, "Session not found", http.StatusNotFound)
		return
	}

	// Write to stdin
	if session.Process.Stdin != nil {
		session.Process.Stdin.Write([]byte(req.Keys))
	}

	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
	})
}

func handleScreen(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["id"]

	store.mu.RLock()
	session, ok := store.sessions[sessionID]
	store.mu.RUnlock()

	if !ok {
		http.Error(w, "Session not found", http.StatusNotFound)
		return
	}

	session.Mu.Lock()
	content := string(session.Buffer)
	session.Mu.Unlock()

	json.NewEncoder(w).Encode(map[string]interface{}{
		"type":    "text",
		"content": content,
	})
}

func handleResize(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["id"]

	var req struct {
		Cols int `json:"cols"`
		Rows int `json:"rows"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
	})
}

func handleKill(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["id"]

	store.mu.Lock()
	session, ok := store.sessions[sessionID]
	if ok {
		delete(store.sessions, sessionID)
	}
	store.mu.Unlock()

	if !ok {
		http.Error(w, "Session not found", http.StatusNotFound)
		return
	}

	if session.Process.Process != nil {
		session.Process.Process.Kill()
	}

	log.Printf("Session %s killed", sessionID)

	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
	})
}

func generateID() string {
	// Simple ID generation - can be improved with UUID
	return "sess_" + randomString(8)
}

func randomString(n int) string {
	const letters = "abcdefghijklmnopqrstuvwxyz0123456789"
	b := make([]byte, n)
	for i := range b {
		b[i] = letters[i%len(letters)]
	}
	return string(b)
}
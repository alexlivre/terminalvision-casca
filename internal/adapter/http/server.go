package adapter

import (
	"encoding/json"
	"log"
	"net/http"
	"strconv"

	"github.com/gorilla/mux"
	"localcasca/internal/domain"
	"localcasca/internal/usecase"
)

// Server handles HTTP requests
type Server struct {
	router  *mux.Router
	manager *usecase.SessionManager
}

// NewServer creates a new HTTP server
func NewServer() *Server {
	return &Server{
		router:  mux.NewRouter(),
		manager: usecase.NewSessionManager(),
	}
}

// SetupRoutes configures all routes
func (s *Server) SetupRoutes() {
	s.router.HandleFunc("/terminal/spawn", s.handleSpawn).Methods("POST")
	s.router.HandleFunc("/terminal/list", s.handleList).Methods("GET")
	s.router.HandleFunc("/terminal/{id}", s.handleGet).Methods("GET")
	s.router.HandleFunc("/terminal/{id}", s.handleKill).Methods("DELETE")
	s.router.HandleFunc("/terminal/{id}/screen", s.handleScreen).Methods("GET")
	s.router.HandleFunc("/terminal/{id}/keys", s.handleKeys).Methods("POST")
	s.router.HandleFunc("/terminal/{id}/resize", s.handleResize).Methods("POST")
	s.router.HandleFunc("/terminal/{id}/wait", s.handleWait).Methods("GET")
	s.router.HandleFunc("/health", s.handleHealth).Methods("GET")
	s.router.HandleFunc("/metrics", s.handleMetrics).Methods("GET")
}

// Router returns the configured router
func (s *Server) Router() *mux.Router {
	return s.router
}

func jsonResponse(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

func (s *Server) handleSpawn(w http.ResponseWriter, r *http.Request) {
	var req domain.SpawnRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		jsonResponse(w, http.StatusBadRequest, domain.ErrorResponse{Error: "invalid request: " + err.Error()})
		return
	}
	resp, err := s.manager.Spawn(req)
	if err != nil {
		log.Printf("Spawn error: %v", err)
		jsonResponse(w, http.StatusInternalServerError, domain.ErrorResponse{Error: err.Error()})
		return
	}
	jsonResponse(w, http.StatusCreated, resp)
}

func (s *Server) handleList(w http.ResponseWriter, r *http.Request) {
	jsonResponse(w, http.StatusOK, s.manager.List())
}

func (s *Server) handleGet(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["id"]
	for _, sess := range s.manager.List().Sessions {
		if sess["session_id"] == sessionID {
			jsonResponse(w, http.StatusOK, sess)
			return
		}
	}
	jsonResponse(w, http.StatusNotFound, domain.ErrorResponse{Error: "session not found"})
}

func (s *Server) handleScreen(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["id"]
	format := r.URL.Query().Get("format")
	if format == "" {
		format = "text"
	}
	resp, err := s.manager.GetScreen(sessionID, format)
	if err != nil {
		jsonResponse(w, http.StatusNotFound, domain.ErrorResponse{Error: err.Error()})
		return
	}
	jsonResponse(w, http.StatusOK, resp)
}

func (s *Server) handleKeys(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["id"]
	var req domain.KeysRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		jsonResponse(w, http.StatusBadRequest, domain.ErrorResponse{Error: "invalid request: " + err.Error()})
		return
	}
	resp, err := s.manager.SendKeys(sessionID, req)
	if err != nil {
		jsonResponse(w, http.StatusNotFound, domain.ErrorResponse{Error: err.Error()})
		return
	}
	jsonResponse(w, http.StatusOK, resp)
}

func (s *Server) handleResize(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["id"]
	var req domain.ResizeRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		jsonResponse(w, http.StatusBadRequest, domain.ErrorResponse{Error: "invalid request: " + err.Error()})
		return
	}
	resp, err := s.manager.Resize(sessionID, req.Cols, req.Rows)
	if err != nil {
		jsonResponse(w, http.StatusNotFound, domain.ErrorResponse{Error: err.Error()})
		return
	}
	jsonResponse(w, http.StatusOK, resp)
}

func (s *Server) handleWait(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["id"]
	condition := r.URL.Query().Get("condition")
	timeoutStr := r.URL.Query().Get("timeout_ms")
	if condition == "" {
		jsonResponse(w, http.StatusBadRequest, domain.ErrorResponse{Error: "condition required"})
		return
	}
	timeoutMs := 10000
	if timeoutStr != "" {
		if t, err := strconv.Atoi(timeoutStr); err == nil {
			timeoutMs = t
		}
	}
	req := domain.WaitRequest{Condition: condition, TimeoutMs: timeoutMs}
	resp, err := s.manager.Wait(sessionID, req)
	if err != nil {
		jsonResponse(w, http.StatusNotFound, domain.ErrorResponse{Error: err.Error()})
		return
	}
	jsonResponse(w, http.StatusOK, resp)
}

func (s *Server) handleKill(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["id"]
	resp, err := s.manager.Kill(sessionID)
	if err != nil {
		jsonResponse(w, http.StatusNotFound, domain.ErrorResponse{Error: err.Error()})
		return
	}
	jsonResponse(w, http.StatusOK, resp)
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	jsonResponse(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *Server) handleMetrics(w http.ResponseWriter, r *http.Request) {
	resp := s.manager.List()
	jsonResponse(w, http.StatusOK, map[string]interface{}{"active_sessions": len(resp.Sessions), "sessions": resp.Sessions})
}
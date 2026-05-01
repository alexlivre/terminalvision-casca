package api

import (
	"encoding/json"
	"net/http"

	"github.com/gorilla/mux"
)

type Router struct {
	mux *mux.Router
}

func NewRouter() *http.ServeMux {
	r := mux.NewRouter()

	// Register routes
	r.HandleFunc("/terminal/spawn", handleSpawn).Methods("POST")
	r.HandleFunc("/terminal/list", handleList).Methods("GET")
	r.HandleFunc("/terminal/{id}/send", handleSend).Methods("POST")
	r.HandleFunc("/terminal/{id}/screen", handleScreen).Methods("GET")
	r.HandleFunc("/terminal/{id}/resize", handleResize).Methods("POST")
	r.HandleFunc("/terminal/{id}", handleKill).Methods("DELETE")
	r.HandleFunc("/health", handleHealth).Methods("GET")

	return r
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}
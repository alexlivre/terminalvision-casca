package main

import (
	"log"
	"net/http"
	"os"

	"github.com/alexlivre/terminalvision-casca/internal/adapter/http"
)

func main() {
	port := os.Getenv("CASCA_PORT")
	if port == "" {
		port = "8787"
	}

	server := adapter.NewServer()
	server.SetupRoutes()

	log.Printf("CASCA starting on :%s", port)
	log.Printf("API endpoints: http://localhost:%s/terminal/*", port)
	log.Printf("Health check: http://localhost:%s/health", port)

	if err := http.ListenAndServe(":"+port, server.Router()); err != nil {
		log.Fatal(err)
	}
}

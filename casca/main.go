package main

import (
	"log"
	"net/http"
	"os"

	"github.com/terminalvision/casca/api"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8787"
	}

	router := api.NewRouter()

	log.Printf("CASCA starting on :%s", port)
	log.Printf("API endpoints: http://localhost:%s/terminal/*", port)

	if err := http.ListenAndServe(":"+port, router); err != nil {
		log.Fatal(err)
	}
}
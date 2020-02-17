package main

import (
	"fmt"
	"net/http"
)

func home(w http.ResponseWriter, req *http.Request) {

	fmt.Fprintf(w, "Home\n")
}

func main() {

	http.HandleFunc("/", home)

	http.ListenAndServe(":8090", nil)
}

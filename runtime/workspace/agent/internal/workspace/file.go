package workspace

import (
	"encoding/json"
	"io"
	"net/http"
	"os"
	"path"
	"path/filepath"
	"strings"
)

func (a *agent) fileHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		filePath, ok := requestedFilePath(r)
		if !ok {
			http.Error(w, "file path must be absolute", http.StatusBadRequest)
			return
		}

		switch r.Method {
		case http.MethodGet:
			serveFile(w, r, filePath)
		case http.MethodPut:
			writeFile(w, r, filePath)
		case http.MethodDelete:
			deleteFile(w, filePath)
		default:
			w.Header().Set("Allow", "GET, PUT, DELETE")
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	}
}

func requestedFilePath(r *http.Request) (string, bool) {
	rawPath := strings.TrimPrefix(r.URL.Path, "/file")
	filePath := path.Clean("/" + strings.TrimPrefix(rawPath, "/"))
	return filePath, filepath.IsAbs(filePath)
}

func serveFile(w http.ResponseWriter, r *http.Request, filePath string) {
	stat, err := os.Stat(filePath)
	if err != nil {
		httpError(w, err)
		return
	}
	if stat.IsDir() {
		entries, err := os.ReadDir(filePath)
		if err != nil {
			httpError(w, err)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		names := make([]string, 0, len(entries))
		for _, entry := range entries {
			names = append(names, entry.Name())
		}
		_ = json.NewEncoder(w).Encode(names)
		return
	}
	http.ServeFile(w, r, filePath)
}

func writeFile(w http.ResponseWriter, r *http.Request, filePath string) {
	if err := os.MkdirAll(filepath.Dir(filePath), 0755); err != nil {
		httpError(w, err)
		return
	}
	file, err := os.OpenFile(filePath, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
	if err != nil {
		httpError(w, err)
		return
	}
	defer file.Close()
	if _, err := io.Copy(file, r.Body); err != nil {
		httpError(w, err)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func deleteFile(w http.ResponseWriter, filePath string) {
	if filePath == "/" {
		http.Error(w, "refusing to delete filesystem root", http.StatusBadRequest)
		return
	}
	if err := os.RemoveAll(filePath); err != nil {
		httpError(w, err)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func httpError(w http.ResponseWriter, err error) {
	if os.IsNotExist(err) {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}
	if os.IsPermission(err) {
		http.Error(w, err.Error(), http.StatusForbidden)
		return
	}
	http.Error(w, err.Error(), http.StatusInternalServerError)
}

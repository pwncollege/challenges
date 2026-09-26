package daemon

import (
	"fmt"
	"os"
	"path/filepath"
)

// Write and fsync before publishing a record. These records survive daemon and
// host restarts; losing a response must not replay initialization or a handoff.
func recordRequest(path, value string) error {
	if data, err := os.ReadFile(path); err == nil {
		if string(data) != value {
			return fmt.Errorf("operation has different parameters")
		}
		return nil
	} else if !os.IsNotExist(err) {
		return err
	}
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0711); err != nil {
		return err
	}
	if err := syncDirectory(filepath.Dir(dir)); err != nil {
		return err
	}
	file, err := os.CreateTemp(dir, ".record-")
	if err != nil {
		return err
	}
	defer os.Remove(file.Name())
	defer file.Close()
	if _, err := file.WriteString(value); err != nil {
		return err
	}
	if err := file.Sync(); err != nil {
		return err
	}
	if err := file.Close(); err != nil {
		return err
	}
	if err := os.Rename(file.Name(), path); err != nil {
		return err
	}
	return syncDirectory(dir)
}

func syncDirectory(path string) error {
	dir, err := os.Open(path)
	if err != nil {
		return err
	}
	defer dir.Close()
	return dir.Sync()
}

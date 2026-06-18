package workspace

import (
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"syscall"

	"github.com/coder/websocket"
	"github.com/creack/pty"
)

const defaultPtyRows = 24
const defaultPtyCols = 80

type ptyMessage struct {
	Type string `json:"type"`
	Rows uint16 `json:"rows"`
	Cols uint16 `json:"cols"`
}

func (a *agent) ptySocket() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		conn, err := websocket.Accept(w, r, &websocket.AcceptOptions{
			InsecureSkipVerify: true,
		})
		if err != nil {
			a.logger.Warn("websocket accept failed", "err", err)
			return
		}
		defer conn.Close(websocket.StatusInternalError, "workspace pty closed unexpectedly")

		ctx := r.Context()
		command := ptyCommand()
		cmd := exec.CommandContext(ctx, command[0], command[1:]...)
		cmd.Dir = ptyCwd()
		cmd.Env = append(os.Environ(), "TERM=xterm-256color")

		terminal, err := pty.StartWithAttrs(
			cmd,
			&pty.Winsize{Rows: defaultPtyRows, Cols: defaultPtyCols},
			&syscall.SysProcAttr{
				Setsid:  true,
				Setctty: true,
				Ctty:    0,
			},
		)
		if err != nil {
			a.logger.Warn("pty start failed", "err", err)
			conn.Close(websocket.StatusInternalError, "pty start failed")
			return
		}
		defer terminal.Close()

		waitDone := make(chan error, 1)
		go func() {
			waitDone <- cmd.Wait()
		}()

		outputDone := make(chan error, 1)
		go func() {
			buffer := make([]byte, 32*1024)
			for {
				n, readErr := terminal.Read(buffer)
				if n > 0 {
					if err := conn.Write(ctx, websocket.MessageBinary, buffer[:n]); err != nil {
						outputDone <- err
						return
					}
				}
				if readErr != nil {
					if errors.Is(readErr, os.ErrClosed) || errors.Is(readErr, io.EOF) {
						outputDone <- nil
					} else {
						outputDone <- readErr
					}
					return
				}
			}
		}()

		inputDone := make(chan error, 1)
		go func() {
			for {
				messageType, reader, err := conn.Reader(ctx)
				if err != nil {
					inputDone <- err
					return
				}
				switch messageType {
				case websocket.MessageBinary:
					_, err = io.Copy(terminal, reader)
				case websocket.MessageText:
					err = handlePtyControl(terminal, reader)
				default:
					_, err = io.Copy(io.Discard, reader)
				}
				if err != nil {
					inputDone <- err
					return
				}
			}
		}()

		select {
		case <-waitDone:
			conn.Close(websocket.StatusNormalClosure, "pty exited")
		case <-outputDone:
			killProcessGroup(cmd)
			conn.Close(websocket.StatusNormalClosure, "pty output closed")
			<-waitDone
		case <-inputDone:
			killProcessGroup(cmd)
			<-waitDone
		case <-ctx.Done():
			killProcessGroup(cmd)
			<-waitDone
		}
	}
}

func handlePtyControl(terminal *os.File, reader io.Reader) error {
	var message ptyMessage
	if err := json.NewDecoder(reader).Decode(&message); err != nil {
		return err
	}
	if message.Type != "resize" {
		return nil
	}
	if message.Rows == 0 || message.Cols == 0 {
		return nil
	}
	return pty.Setsize(terminal, &pty.Winsize{Rows: message.Rows, Cols: message.Cols})
}

func killProcessGroup(cmd *exec.Cmd) {
	if cmd.Process == nil {
		return
	}
	_ = syscall.Kill(-cmd.Process.Pid, syscall.SIGKILL)
}

func ptyCommand() []string {
	if command := os.Getenv("WORKSPACE_PTY_COMMAND"); command != "" {
		return strings.Fields(command)
	}
	if _, err := os.Stat("/bin/bash"); err == nil {
		return []string{"/bin/bash"}
	}
	return []string{"/bin/sh"}
}

func ptyCwd() string {
	if cwd := os.Getenv("WORKSPACE_PTY_CWD"); cwd != "" {
		return cwd
	}
	if home := os.Getenv("HOME"); home != "" {
		if stat, err := os.Stat(home); err == nil && stat.IsDir() {
			return home
		}
	}
	return "/"
}

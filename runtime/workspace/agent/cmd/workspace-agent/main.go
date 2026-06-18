package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"pwn.college/runtime/workspace/internal/workspace"
)

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	if err := workspace.RunAgent(ctx); err != nil {
		slog.New(slog.NewTextHandler(os.Stderr, nil)).Error("workspace agent failed", "err", err)
		os.Exit(1)
	}
}

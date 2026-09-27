package main

import (
	"context"
	"log"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	runtimeapi "k8s.io/cri-api/pkg/apis/runtime/v1"
	daemon "pwn.college/workspace/platform/daemon/internal"
)

func main() {
	cfg, err := daemon.LoadConfig()
	if err != nil {
		log.Fatal(err)
	}
	if err := cfg.PrepareStorage(); err != nil {
		log.Fatal(err)
	}
	containerd, err := grpc.NewClient(
		cfg.ContainerdAddress(),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		log.Fatal(err)
	}
	defer containerd.Close()
	workspaceDaemon := daemon.New(
		cfg,
		runtimeapi.NewRuntimeServiceClient(containerd),
		runtimeapi.NewImageServiceClient(containerd),
	)

	bootstrapContext, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	if err := workspaceDaemon.Bootstrap(bootstrapContext); err != nil {
		log.Fatal(err)
	}
	if err := workspaceDaemon.Serve(); err != nil {
		log.Fatal(err)
	}
}

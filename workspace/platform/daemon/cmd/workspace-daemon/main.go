package main

import (
	"context"
	"log"
	"time"

	dockerclient "github.com/docker/docker/client"
	daemon "pwn.college/workspace/platform/daemon/internal"
)

func main() {
	cfg, err := daemon.LoadConfig()
	if err != nil {
		log.Fatal(err)
	}
	docker, err := dockerclient.NewClientWithOpts(
		dockerclient.FromEnv,
		dockerclient.WithAPIVersionNegotiation(),
	)
	if err != nil {
		log.Fatal(err)
	}
	workspaceDaemon := daemon.New(cfg, docker)

	bootstrapContext, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	if err := workspaceDaemon.Bootstrap(bootstrapContext); err != nil {
		log.Fatal(err)
	}
	if err := workspaceDaemon.Serve(); err != nil {
		log.Fatal(err)
	}
}

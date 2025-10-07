IMAGE_SHORT_NAME := git-keeper
IMAGE_TAG := $(shell git rev-parse --short=7 HEAD)

ifneq (,$(wildcard $(CURDIR)/.docker))
	DOCKER_CONF := $(CURDIR)/.docker
else
	DOCKER_CONF := $(HOME)/.docker
endif

.PHONY: test
test:
	docker build -f dockerfiles/Dockerfile --target test -t $(IMAGE_SHORT_NAME)-test:latest .

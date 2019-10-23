IMAGE_SHORT_NAME := git-keeper
IMAGE_NAME := quay.io/app-sre/$(IMAGE_SHORT_NAME)
IMAGE_TAG := $(shell git rev-parse --short=7 HEAD)

ifneq (,$(wildcard $(CURDIR)/.docker))
	DOCKER_CONF := $(CURDIR)/.docker
else
	DOCKER_CONF := $(HOME)/.docker
endif

.PHONY: test
test:
	docker build -f dockerfiles/Dockerfile.test -t $(IMAGE_SHORT_NAME)-test:latest .
	docker run $(IMAGE_SHORT_NAME)-test:latest tox

.PHONY: build
build:
	@docker build -f dockerfiles/Dockerfile -t $(IMAGE_NAME):latest .
	@docker tag $(IMAGE_NAME):latest $(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: push
push:
	@docker --config=$(DOCKER_CONF) push $(IMAGE_NAME):latest
	@docker --config=$(DOCKER_CONF) push $(IMAGE_NAME):$(IMAGE_TAG)

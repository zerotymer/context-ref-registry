VERSION  ?= 1.0.0
HUB_ORG   = zerotymer
NEXUS     = nexus.zerotymer.net/docker
PLATFORM  = linux/amd64

API_LOCAL   = llm-registry-api:build
FRONT_LOCAL = llm-registry-front:build

.PHONY: build tag push release clean

## Build local images
build:
	docker build --platform $(PLATFORM) -t $(API_LOCAL)   ./backend
	docker build --platform $(PLATFORM) -t $(FRONT_LOCAL) ./frontend

## Tag local images → 8 remote tags
tag:
	docker tag $(API_LOCAL)   $(HUB_ORG)/llm-registry-api:latest
	docker tag $(API_LOCAL)   $(HUB_ORG)/llm-registry-api:$(VERSION)
	docker tag $(API_LOCAL)   $(NEXUS)/llm-registry-api:latest
	docker tag $(API_LOCAL)   $(NEXUS)/llm-registry-api:$(VERSION)
	docker tag $(FRONT_LOCAL) $(HUB_ORG)/llm-registry-front:latest
	docker tag $(FRONT_LOCAL) $(HUB_ORG)/llm-registry-front:$(VERSION)
	docker tag $(FRONT_LOCAL) $(NEXUS)/llm-registry-front:latest
	docker tag $(FRONT_LOCAL) $(NEXUS)/llm-registry-front:$(VERSION)

## Push all 8 tags to both registries
push:
	docker push $(HUB_ORG)/llm-registry-api:latest
	docker push $(HUB_ORG)/llm-registry-api:$(VERSION)
	docker push $(NEXUS)/llm-registry-api:latest
	docker push $(NEXUS)/llm-registry-api:$(VERSION)
	docker push $(HUB_ORG)/llm-registry-front:latest
	docker push $(HUB_ORG)/llm-registry-front:$(VERSION)
	docker push $(NEXUS)/llm-registry-front:latest
	docker push $(NEXUS)/llm-registry-front:$(VERSION)

## Full release: build → tag → push
release: build tag push

## Remove local build images
clean:
	docker rmi -f $(API_LOCAL) $(FRONT_LOCAL) 2>/dev/null || true

VERSION  ?= 1.0.0
HUB_ORG   = zerotymer
PLATFORM  = linux/amd64

API_LOCAL   = llm-registry-api:build
FRONT_LOCAL = llm-registry-front:build

.PHONY: build tag push release clean

## Build local images (API needs NEXUS_PYPI_URL — credentialed Nexus PyPI index URL)
build:
	@test -n "$$NEXUS_PYPI_URL" || (echo "NEXUS_PYPI_URL is not set" && exit 1)
	docker build --platform $(PLATFORM) --secret id=nexus_pypi,env=NEXUS_PYPI_URL -t $(API_LOCAL) ./backend
	docker build --platform $(PLATFORM) -t $(FRONT_LOCAL) ./frontend

## Tag local images → 4 Docker Hub tags
tag:
	docker tag $(API_LOCAL)   $(HUB_ORG)/llm-registry-api:latest
	docker tag $(API_LOCAL)   $(HUB_ORG)/llm-registry-api:$(VERSION)
	docker tag $(FRONT_LOCAL) $(HUB_ORG)/llm-registry-front:latest
	docker tag $(FRONT_LOCAL) $(HUB_ORG)/llm-registry-front:$(VERSION)

## Push all 4 tags to Docker Hub (Nexus is an install proxy only — never push there)
push:
	docker push $(HUB_ORG)/llm-registry-api:latest
	docker push $(HUB_ORG)/llm-registry-api:$(VERSION)
	docker push $(HUB_ORG)/llm-registry-front:latest
	docker push $(HUB_ORG)/llm-registry-front:$(VERSION)

## Full release: build → tag → push
release: build tag push

## Remove local build images
clean:
	docker rmi -f $(API_LOCAL) $(FRONT_LOCAL) 2>/dev/null || true

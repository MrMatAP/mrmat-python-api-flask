#
# Convenience Makefile
# Useful reference: https://makefiletutorial.com

GIT_SHA := $(shell git rev-parse --short HEAD)
VERSION ?= 0.0.0-dev0.${GIT_SHA}
PYTHON_VERSION := $(shell echo "${VERSION}" | sed -e 's/-dev0\./-dev0+/')
WHEEL_VERSION := $(shell echo "${VERSION}" | sed -e 's/-dev0\./.dev0+/')

ROOT_PATH := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

PYTHON_SOURCES := $(shell find src/mrmat_python_api_flask -name '*.py')
PYTHON_TARGET := dist/mrmat_python_api_flask-${WHEEL_VERSION}-py3-none-any.whl
CONTAINER_SOURCES := $(shell find var/container)
HELM_SOURCES := $(shell find var/helm)
HELM_TARGET := dist/mrmat-python-api-flask-$(VERSION).tgz

all: python container helm
python: $(PYTHON_TARGET)
helm: $(HELM_TARGET)

$(PYTHON_TARGET): $(PYTHON_SOURCES)
	MRMAT_VERSION="${PYTHON_VERSION}" python -mbuild -n --wheel

$(HELM_TARGET): $(HELM_SOURCES) container
	helm package \
		--app-version "$(VERSION)" \
		--version $(VERSION) \
		--destination dist/ \
		var/helm

container: $(PYTHON_TARGET) $(CONTAINER_SOURCES)
	docker build \
		-f var/container/Dockerfile \
		-t localhost:5001/mrmat-python-api-flask:$(VERSION) \
		--build-arg MRMAT_VERSION=$(VERSION) \
		--build-arg WHEEL=$(PYTHON_TARGET) \
		$(ROOT_PATH)
	docker push localhost:5001/mrmat-python-api-flask:$(VERSION)

helm-install: $(HELM_TARGET)
	kubectl create ns mpaflask || true
	kubectl label --overwrite ns mpaflask istio-injection=true
	helm upgrade \
		mrmat-python-api-flask \
		${HELM_TARGET} \
		--install \
		--force \
		--namespace mpaflask

helm-uninstall:
	helm delete -n mpaflask mrmat-python-api-flask

clean:
	rm -rf build dist

# Copyright (C) 2017 Platform9 Systems, Inc.


SRCROOT = $(abspath $(dir $(CURDIR)/../$(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST))))
PF9APP = $(SRCROOT)/pf9app

PF9_VERSION ?= 3.1.0
BUILD_NUMBER ?= 0
GITHASH=$(shell git rev-parse --short HEAD)
UID ?= $(shell id -u)
GID ?= $(shell id -g)
CENTOS65_IMG ?= docker-registry.platform9.horse:5000/centos65
BUILD = $(SRCROOT)/build/pf9app/neutron-debug
STAGE = $(BUILD)/stage

.PHONY: all rpm deb rpmstage debstage clean

all: wrapper
wrapper: rpm deb
rpm: rpmstage
deb: debstage
rpmstage: $(STAGE)/rpm
debstage: $(STAGE)/deb

wrapper: rpm deb
	$(PF9APP)/build-wrapper.sh

rpm deb: rpmstage debstage
	$(PF9APP)/package.sh $(PF9_VERSION) $(BUILD_NUMBER) $(STAGE)/$@ $(BUILD) $@

$(STAGE)/rpm $(STAGE)/deb:
	mkdir -p $@
	$(PF9APP)/install-python.sh $@
	pythonbin=$@/opt/pf9/python/bin/python; \
	$(PF9APP)/install-pf9app.sh $@ $${pythonbin} `basename $@`

clean:
	rm -rf $(BUILD)

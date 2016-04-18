.PHONY: test

RUN=bin/msgparse

TESTBIN:=nosetests
TESTARGS:=--verbosity=3
TESTDIR:=$(shell pwd)

all:
	exit 1

test:
	${TESTBIN} ${TESTARGS} ${TESTDIR}

help:
	-${RUN} --help

examples:

	@echo '1) Parse cli args: '
	${RUN} -c '@mary had a (littlelamb) http://dillonhicks.io'
	@echo''

	@echo '2) Parse from a file: '
	@sleep 2

	${RUN} -f tests/sample-messages.txt
	@echo ''
	@echo ''

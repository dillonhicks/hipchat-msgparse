.PHONY: test

TESTBIN:=nosetests
TESTARGS:=--verbosity=3
TESTDIR:=$(shell pwd)

all:
	exit 1

test:
	${TESTBIN} ${TESTARGS} ${TESTDIR}

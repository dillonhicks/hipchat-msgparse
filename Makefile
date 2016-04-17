.PHONY: test

TESTBIN:=nosetests
TESTDIR:=$(shell pwd)

all:
	exit 1

test:
	${TESTBIN} --verbosity=3 ${TESTDIR}

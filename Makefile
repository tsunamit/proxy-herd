# Makefile for proxy-herd project

default: run

# Perform general environment setup. Create python virtualenv
.SILENT: setup env run

install:
	echo "Running first time setup for Python virtualenv: venv..."
	virtualenv -p /usr/local/bin/python3.7 venv
	echo "Done creating environment!"
	
run:
	python server.py Hands 
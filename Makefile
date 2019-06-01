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

goloman:
	python3 server.py Goloman 

hands:
	python3 server.py Hands

holiday:
	python3 server.py Holiday 

welsh:
	python3 server.py Welsh 

wilkes:
	python3 server.py Wilkes 

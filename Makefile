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

test1:
	echo "IAMAT kiwi +0.0-0.0 1520023934.918963997" | nc 127.0.0.1 12778
	echo "WHATSAT kiwi 1 1" | nc 127.0.0.1 12777
	echo "WHATSAT kiwi 1 1" | nc 127.0.0.1 12778
	echo "WHATSAT kiwi 1 1" | nc 127.0.0.1 12779
	echo "WHATSAT kiwi 1 1" | nc 127.0.0.1 12780
	echo "WHATSAT kiwi 1 1" | nc 127.0.0.1 12781
	echo "IAMAT kiwi +1.0-1.0 1520023934.918963997" | nc 127.0.0.1 12778


iamat1:
	echo "IAMAT kiwi +34.068930-118.445127 1520023934.918963997" | nc 127.0.0.1 12777
	echo "IAMAT lemon +6.9-6.9 1520023935.918963997" | nc 127.0.0.1 12781
	echo "IAMAT apple +6.9-6.9 1520023935.918963997" | nc 127.0.0.1 12780
	echo "IAMAT orange +6.9-6.9 1520023935.918963997" | nc 127.0.0.1 12779
	echo "IAMAT pineapple +6.9-6.9 152002399.918963997" | nc 127.0.0.1 12778
	echo "IAMAT kiwi +34.068930-118.445127 1520023939.918963997" | nc 127.0.0.1 12777
	echo "IAMAT lemon +9.9-9.9 1520023935.918993997" | nc 127.0.0.1 12781
	echo "IAMAT apple +9.9-9.9 1520023935.918993997" | nc 127.0.0.1 12780
	echo "IAMAT orange +9.9-9.9 1520023935.918993997" | nc 127.0.0.1 12779
	echo "IAMAT pineapple +9.9-9.9 152002399.918993997" | nc 127.0.0.1 12778

query:
	echo "WHATSAT kiwi 10 5" | nc 127.0.0.1 12777
	echo "WHATSAT kiwi 10 5" | nc 127.0.0.1 12778
	echo "WHATSAT kiwi 10 5" | nc 127.0.0.1 12779
	echo "WHATSAT kiwi 10 5" | nc 127.0.0.1 12780
	echo "WHATSAT kiwi 10 5" | nc 127.0.0.1 12781

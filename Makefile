flake:
	flake8 imgurup

test: flake
	py.test tests.py

cov coverage:
	py.test --cov-report term-missing --cov=imgurup tests.py

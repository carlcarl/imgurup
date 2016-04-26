flake:
	flake8 imgurup

.develop:
	pip install -e .
	touch .develop

test: flake .develop
	py.test

cov coverage: flake .develop
	py.test --cov-report term-missing --cov imgurup

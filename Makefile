test:
	nosetests --with-coverage --cover-package=cabrita --cover-min-percentage=90
	pydocstyle cabrita/
	pycodestyle --max-line-length=120 --exclude=cabrita/tests/__init__.py cabrita/
	mypy -p cabrita --ignore-missing-imports

break:
	nosetests -v --nocapture --ipdb

coverage:
	coverage report -m
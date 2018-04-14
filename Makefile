test:
	nosetests --with-coverage --cover-package=cabrita --cover-min-percentage=90
	pydocstyle --match-dir=cabrita
	pycodestyle outpak/

break:
	nosetests -v --nocapture --ipdb

coverage:
	coverage report -m
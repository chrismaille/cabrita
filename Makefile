test:
	nosetests --with-coverage --cover-package=outpak --cover-min-percentage=80
	pydocstyle --match-dir=outpak
	pycodestyle outpak/

break:
	nosetests -v --nocapture --ipdb

coverage:
	coverage report -m
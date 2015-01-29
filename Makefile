
.PHONY: docs view help

# export all the docs as a static variable:https://gist.github.com/azatoth/1030091
define help_docs

 ** *** ** *** ** *** ** *** ** *** *** ** *** ** *** ** *** ** ***
 ** Old School Maker Power!
 **
 Welcome to the hyperdns/toolkit Makefile!

	- make         - view this message
	- make help    - view this message
	- make env     - regenerate the python virtualenv
	- make docs    - build the documentation
	- make view    - build the documentation and display it in a browser
	- make clean   - remove temporary files
	- make wheel   -
	- make publish -
	- make tarinstaller -

	(simple)
	- make virgin  - install a base python virtual env
	- make locals  - link to local repositories
	- make reqs    - the local python env
	- make self    - install the local package

	(special configuration files required for the following)
	- make gh-pages - build and publish the documentation to github pages
	- make publish  - publish to pypi and update the gh-pages



endef
export help_docs

VERSION := $(shell cat version.txt)

help:
	@echo "$$help_docs"

virgin:
	rm -rf .python
	virtualenv .python -p python3

locals:
	#

reqs:
	. .python/bin/activate && pip install -r requirements.txt -r dev-requirements.txt

self:
	. .python/bin/activate && pip install -e .

env:
	${MAKE} virgin
	${MAKE} locals 
	${MAKE} reqs
	${MAKE} self

wheel:
	. .python/bin/activate && python setup.py bdist_wheel

publish:
	python setup.py sdist upload -r pypi

docs:
	make -C docs html

view:
	python -c "import webbrowser; webbrowser.open('file://$(PWD)/docs/_build/html/index.html')"

gh-pages-internal:
	git checkout gh-pages
	rm -rf *.html *.js _modules _sources _static objects.inv *.egg-info dist
	git checkout master docs hyperdns README.md
	make -C docs html
	mv docs/_build/html/* .
	rm -rf docs hyperdns README.md
	git add -A
	git add _modules
	git commit -m "new gh-pages docs"
	git push origin gh-pages
	git checkout master
	# do *not* understand why _modules is so stuck
	rm -rf _modules
	# add the entry point back
	pip install -e .

gh-pages:
	-$(MAKE) gh-pages-internal
	git stash
	git checkout master

clean:
	rm -rf dist
	rm -rf *.egg-info


.PHONY: all fetch clean analyze maps deliverables test compile pages-ready

PYTHON ?= python

all:
	$(PYTHON) scripts/run_all.py

fetch:
	$(PYTHON) scripts/fetch_data.py
	$(PYTHON) scripts/fetch_boundaries.py
	$(PYTHON) scripts/fetch_context.py
	$(PYTHON) scripts/fetch_demographics.py

clean:
	$(PYTHON) scripts/clean_311_requests.py

analyze:
	$(PYTHON) scripts/analyze_requests.py

maps:
	$(PYTHON) scripts/make_maps.py

deliverables:
	$(PYTHON) scripts/make_deliverables.py

test:
	$(PYTHON) -m unittest discover -s tests

compile:
	$(PYTHON) -m compileall scripts tests

pages-ready: test compile

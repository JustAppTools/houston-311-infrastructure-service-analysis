.PHONY: all fetch clean analyze maps test

PYTHON ?= python

all:
	$(PYTHON) scripts/run_all.py

fetch:
	$(PYTHON) scripts/fetch_data.py
	$(PYTHON) scripts/fetch_boundaries.py
	$(PYTHON) scripts/fetch_demographics.py

clean:
	$(PYTHON) scripts/clean_311_requests.py

analyze:
	$(PYTHON) scripts/analyze_requests.py

maps:
	$(PYTHON) scripts/make_maps.py

test:
	$(PYTHON) -m unittest discover -s tests

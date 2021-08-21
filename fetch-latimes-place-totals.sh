#!/bin/bash
wget -O latimes-place-totals.csv https://github.com/datadesk/california-coronavirus-data/raw/master/latimes-place-totals.csv
pipenv run python latimes-places-import.py
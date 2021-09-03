#!/bin/bash
if [[ $1 = 'fetch' ]]
then
    # echo "Fetching LA Times dataset and parsing sources..."
    bash fetch-latimes-place-totals.sh && bash parse-sources.sh
fi
pipenv run gunicorn app:server
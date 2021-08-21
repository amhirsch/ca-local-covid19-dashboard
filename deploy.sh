#!/bin/bash
bash fetch-latimes-place-totals.sh && bash parse-sources.sh
NAME='ca-local-covid-19-dashboard'
docker buildx build --platform linux/amd64 --tag $NAME . \
    && docker tag $NAME "registry.heroku.com/$NAME/web" \
    && docker push "registry.heroku.com/$NAME/web" \
    && heroku container:release web --app $NAME
# Loading the dev container

From a terminal window, after cd'ing to where the docker-compose is located, run:

> docker compose -f docker-compose.yaml --env-file .env.dev up

You will need an updated version of the .env.dev file.

# Loading the production container locally (for testing purposes)

From a terminal window, after cd'ing to where the docker-compose is located, run:

> docker compose -f docker-compose.prod.yaml --env-file .env.prod up

You will need an updated version of the .env.prod file.

Afterwards, you will need to manually run the fake migrations if it is your first time creating the container and its volumes locally:

> docker compose -f docker-compose.prod.yaml --env-file .env.prod exec web python manage.py migrate --fake 

And if that is the case, you will also need to load the data from the zones.json file

> docker compose -f docker-compose.prod.yaml --env-file .env.prod exec web python manage.py loaddata zones.json

For subsequent executions of the container, so long as you haven't deleted the volumes, these two commands are unnecessary.
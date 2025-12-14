# Umigo

Umigo is a project aiming to help students who come from outside of Bogotá with finding a place of residence during their stay while they course through their career.

# Running the project inside docker containers

## Loading the dev containers

From a terminal window, after cd'ing to where the docker-compose is located, run:

> docker compose -f docker-compose.yaml --env-file .env.dev up

You will need a .env.dev file that includes the information required by the settings.py file and the docker-related files.

## Loading the production containers locally (for testing purposes)

From a terminal window, after cd'ing to where the docker-compose is located, run:

> docker compose -f docker-compose.prod.yaml --env-file .env.prod up

You will need a .env.prod file that includes the information required by the settings.py file and the docker-related files.

Afterwards, you will need to manually run the fake migrations if it is your first time creating the container and its volumes locally:

> docker compose -f docker-compose.prod.yaml --env-file .env.prod exec web python manage.py migrate --fake 

And if that is the case, you will also need to load the data from the zones.json file

> docker compose -f docker-compose.prod.yaml --env-file .env.prod exec web python manage.py loaddata zones.json

For subsequent executions of the container, so long as you haven't deleted the volumes, these two commands are unnecessary.
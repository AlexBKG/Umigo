# Loading the dev container

From a terminal window, after cd'ing to where the docker-compose is located, run:

> docker compose -f docker-compose.yaml --env-file .env.dev up

You will need an updated version of the .env.dev file.

# Loading the production container locally (for testing purposes)

From a terminal window, after cd'ing to where the docker-compose is located, run:

> docker compose -f docker-compose.prod.yaml --env-file .env.prod up

You will need an updated version of the .env.prod file.
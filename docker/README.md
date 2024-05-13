# Docker

You will first need to create an auth0 tenant, see [../terraform/README.md](../terraform/README.md) for instructions!

Then run the following:
````bash
cd docker
# copy sample env file and edit as needed
cp .env.sample .env
````

Follow the instructions/comments in your new .env to correctly edit the file.  Then follow the directions below relevant to your (dev or production) deployment environment.

**Note:** If `docker compose` is not a valid command on your machine, install the `docker-compose` binary and use `docker-compose` in place of `docker compose` in the commands below!


## Run development server

````bash
# build and launch dev site
alias dcd='docker compose -f docker-compose.yml -f docker-compose.dev.yml'
dcd build && dcd up -d
````

Now you can visit the site running on http://localhost:2222


## Run Production Server

````bash
docker compose build && docker compose up -d
````
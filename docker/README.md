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
dcd logs -f # view site logs

# you can also get a shell into the container of one the service's for example:
dcd exec -it backend bash
# then you can run unit tests with:
pytest -v
````

Now you can visit the site running on http://localhost:2222


## Run Production Server
ssh into your production server (if created with terraform see `terraform output` for ssh details) and run the following:

````bash
# ensure dependencies are installed and an ssh key is created
#   NOTE: this script is copied to the server by terraform but is also available at ../terraform/modules/ec2/setup.sh
bash ~/setup.sh

cat ~/.ssh/id_ed25519.pub
````

Add the authentication key printed above to your GitHub account [here](https://github.com/settings/ssh/new).  Then create an "A" record on your domains DNS settings pointing to your produdction server's IP before continuing:

````bash
# create SSL keys for https and clone the site from github:
bash ~/setup.sh -i
# if you have a problem generating your SSL keys, you can directly rerun with:
sudo certbot certonly

# launch production site:
cd ~/thesis_app/docker
cp .env.sample .env
# now edit edit the .env file according to the directions inside

# now you can launch the production site as desired with:
docker compose build && docker compose up -d
docker compose logs -f # view site logs
````

See below for instructions on creating (and restoring from) backups of the site.

## Manage Server

````bash
# backup database to .sql file:
./manage.sh -d

# OR backup database + all site files to a .tgz file:
./manage.sh -b

#### restore database from backup
docker compose up -d db
docker compose exec -it db bash
psql -U postgres
# now inside psql delete database if it exists, and create a new empty one:
drop database thesis;
create database thesis;

# now exit psql and run:
ls -al /backups
# pick the .sql file you want to import and run:
psql -U postgres -d thesis < /backups/example.sql
````

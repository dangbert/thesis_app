#!/bin/bash
set -e

SCRIPT_DIR="$(realpath "$(dirname "$0")")"

VOLUMES_DIR="$SCRIPT_DIR/volumes"
DB_NAME="thesis"

# alias dc='docker compose'
# alias dc='docker compose -f docker-compose.yml -f docker-compose.dev.yml'

function main() {
    cd "$SCRIPT_DIR"
    RAN=0

    # (place a colon between args if a value is expected following that option)
    while getopts "hdbl" arg; do
        case $arg in
        h)
            usage
            RAN=1
            ;;
        l)
            relaunch
            RAN=1
            ;;

        d)
            db_dump
            #relaunch
            RAN=1
            ;;
        b)
            full_backup
            #relaunch
            RAN=1
            ;;
        esac
    done

    if [ $RAN -eq 0 ]; then
        usage
        exit 1
    fi
}

function usage() {
    echo -e "Helper script for managing site deployment."
    echo -e "\nUSAGE:"
    #echo -e "\tmanage.sh [-b] [-d] [-h]\n"
    echo -e "\tmanage.sh -b    # backup ALL site data to .tgz"
    echo -e "\tmanage.sh -d    # dump just database data to .sql file"
    echo -e "\tmanage.sh -l    # relaunch the site"
    echo -e "\tmanage.sh -h    # show this help message"
}


function relaunch {
    echo -e "\nrelaunching site..."
    docker compose down
    docker compose up -d

    sleep 5s
    docker compose ps
}

function db_dump {
    # shouldn't be necessary to stop everything just to dump the DB
    # docker compose down
    # docker compose up -d db
    # echo "sleeping 10sec for DB to startup"
    # sleep 10
    fname="${DB_NAME}_$(date -u '+%F-%T').sql"
    fullFname="$VOLUMES_DIR/backups/$fname"
    docker compose exec -it db bash -c "pg_dump -h localhost -p 5432 -U postgres $DB_NAME > /backups/$fname"

    # with 'set -e' this check isn't needed...
    exitCode="$?"
    if [ $exitCode == 0 ]; then
        echo -e "\nDatabase successfully dumped to '$fullFname'"
    else
        echo -e "\nDatabase dump to '$fullFname' failed with exit code $exitCode"
    fi
}

function full_backup {
    #db_dump
    mkdir -p "$SCRIPT_DIR/full_backups"
    fname="$SCRIPT_DIR/full_backups/volumes_`date -u '+%F-%T'`.tgz"

    # absolute paths are bad for tar commands https://unix.stackexchange.com/a/59246
    relVolumesDir="$(realpath --relative-to="$PWD" "$VOLUMES_DIR")"
    echo "relVolumesDir=$relVolumesDir"
    sudo tar -cvzf "$fname" "$relVolumesDir"
    exitCode="$?"
    echo -e "\nvolumes dir backed up to '$fname' (tar exitCode=$exitCode)"
}

function renew_ssl {
    docker compose down
    sudo certbot renew
    echo -e "\ncertbox certificates"
    certbot certificates
    docker compose up -d
}

main "$@"

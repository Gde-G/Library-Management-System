#!/bin/sh

if [ "$DATABASE" = "mysql" ]
then
    echo "Waiting for MySQL ..."

    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done

    echo "MySQL started"
fi

exec "$@"

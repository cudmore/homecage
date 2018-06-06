Goal here is to abstract the Raspberry Pi GPIO into a class such that the code can be run in multiple workers/threads in either a gunicorn or uwsgi/nginx context.

Problem is that when run with multiple workers/threads, we get hit with GPIO callbacks/events multiple times.

This is in development and does not work out of the box

## Concepts

We need to use a persistent database, in this case we are using redis.

There can be no local (persistent) variables in the code as we have any number of copies of the code running at the same time. All variables to be chared between these processes need to be pickled, stored in a global redis database, and then (un)pickled on retreiving them again.

Important to keep in mind the concept of a database lock as multiple processes may be checking out and modifying database entries.

## Requires

 - Flask
 - GPIO
 - Redis
 

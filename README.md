# Dockerized Flask Visit Counter

A small Flask application counts HTTP requests using Redis. The Flask server and
Redis run in separate containers on a user-defined Docker bridge network.

## Files

- `app/app.py` — Flask routes and the Redis-backed per-request counter.
- `app/requirements.txt` — Python dependencies.
- `Dockerfile` — builds the Flask application image.
- `docker-compose.yml` — defines the app, Redis, network, volume, and Redis health check.
- `.dockerignore` — excludes local and test files from the application image.
- `.gitignore` — excludes Python cache files, local environments, and environment secrets.
- `tests/test_app.py` — unit tests for counting and Redis error handling.

## How it works

Before Flask handles any HTTP request, it runs Redis `INCR` on the `visits` key.
Redis performs this increment atomically, so concurrent requests do not overwrite
one another. The response from `/`, `/increment`, or `/showCurrentCount` is JSON,
for example `{"visits": 1}`.

All requests reaching Flask count, including requests to an unknown route (which
still receive Flask's normal 404 response). A Redis error is logged and results
in HTTP 503 rather than a misleading successful count.

The app connects to Redis by the Compose service hostname `redis`, not
`localhost`. Only the app's port is published on the host; Redis port 6379 is
available to the app over the custom `visit-network` bridge network and is not
published to the host.

The named `redis-data` volume stores Redis data. Append-only-file persistence
(`appendonly yes`) is enabled so the counter is retained when the Redis
container is recreated while the volume remains. This is a simple development
assignment setup, not a production high-availability deployment.

## Prerequisites

- Docker Desktop (or Docker Engine) with the Compose plugin.
- Host port 5000 available.

The project's active Python virtual environment is not needed for the
containerized app; Docker installs the dependencies listed in
`app/requirements.txt`.

## Build and start

Run these commands in the project directory:

```powershell
docker compose up --build -d
docker compose ps
```

Compose starts Redis, waits for its `PING` health check to pass, then starts the
Flask server. The app is reachable from the host at `http://localhost:5000`.

## Test from the host

Each request increments the shared counter once. On a new Redis volume, this
example returns `1`, then `2`, then `3`:

```powershell
curl.exe http://localhost:5000/increment
curl.exe http://localhost:5000/showCurrentCount
curl.exe http://localhost:5000/
```

Each response is JSON, such as `{"visits":2}`. You can also open either
`http://localhost:5000/increment` or
`http://localhost:5000/showCurrentCount` in a browser. Loading the page is a
request and increments the count.

The examples assume a fresh Redis volume. If the project has already been run,
the returned numbers continue from the saved count.

## Verify the network and Redis value

Show the network and its connected containers:

```powershell
docker network inspect visit-network
```

The output should list both the `app` and `redis` containers. You can also see
the Compose service status with `docker compose ps`.

Read the current counter directly from Redis:

```powershell
docker compose exec redis redis-cli GET visits
```

Redis returns the stored number, or `(nil)` before the first app request.
Increment and read it directly for demonstration if desired:

```powershell
docker compose exec redis redis-cli INCR visits
docker compose exec redis redis-cli GET visits
```

Direct Redis commands also change the same counter used by the app.

## Persistence and cleanup

- Restarting or rebuilding the Flask container does not reset the counter.
- Restarting/recreating Redis preserves the counter as long as the named
  `redis-data` volume is retained.
- `docker compose down` stops and removes the containers but keeps the volume.
- `docker compose down -v` also removes the volume and permanently deletes its
  stored counter data.

Stop the containers while preserving the data:

```powershell
docker compose down
```

To start again, run `docker compose up --build -d`.

## Run the unit tests

With Python and the dependencies installed in a local environment:

```powershell
python -m pip install -r app/requirements.txt
python -m unittest discover -s tests -v
```

The tests mock Redis and do not require a running Redis server. Redis
connectivity and container networking are exercised when you run the Compose
stack.

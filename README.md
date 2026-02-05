# landscape-locust

Load testing tool for Landscape to simulate messages from Landscape Client instances.

## Setup

Make sure you have [`uv` installed](https://docs.astral.sh/uv/getting-started/installation/).

Then, install the dependencies with `uv sync`.

This repo contains modules to test different Landscape services.

## Modules

### Pingserver

To run the Pingsever load testing, use the following Make recipe, and modify `HOST` to match the URL of Landscape Server:

```sh
make HOST=https://landscape-server-noble.com/ ping-spam
```

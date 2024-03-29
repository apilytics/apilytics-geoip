# Apilytics GeoIP

[![ci](https://github.com/apilytics/apilytics-geoip/actions/workflows/ci.yml/badge.svg)](https://github.com/apilytics/apilytics-geoip/actions)

## Prerequisites

- [Docker](https://www.docker.com)

## Get the development environment up and running

1. Clone this repository with: `git clone git@github.com:apilytics/apilytics-geoip.git`

2. `cd apilytics-geoip`

3. [Follow the instructions for environment variables](#environment-variables)

4. Build the images: `docker-compose build`

5. Run the app: `docker-compose up`

6. Access the API from [localhost:8000](http://localhost:8000).
   Import the provided [Insomnia file](./Insomnia.yaml) into [Insomnia](https://insomnia.rest/download) for easily trying out the API.

## Environment variables

- Copy the template env file: `cp .env.template .env`

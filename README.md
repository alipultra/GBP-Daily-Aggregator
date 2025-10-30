# Daily Aggregator

"Daily Aggregator" — An API that aggregates learning logs and returns moving averages

## Overview
A Django REST API system for tracking and analyzing study records with word count and study time metrics. The system provides data aggregation and summary capabilities with various granularities.

## Algorithm Explanation
## Core Aggregation Algorithm
The system uses Django's database aggregation functions to summarize study data:

## Initial Setup

- uv is recommended for managing virtual environments.

```
uv sync --all-groups

uv run manage.py migrate
```

### Run tests

```
uv run poe test
```

### Run server

```
uv run manage.py runserver
```


### Lint and format code

```
uv run poe lint
uv run poe format
```

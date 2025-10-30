# Daily Aggregator

"Daily Aggregator" — An API that aggregates learning logs and returns moving averages

## Overview
A Django REST API system for tracking and analyzing study records with word count and study time metrics. The system provides data aggregation and summary capabilities with various granularities.

## Algorithm Explanation
## Core Aggregation Algorithm
The system uses Django's database aggregation functions to summarize study data:
```
# Pseudocode for aggregation service
FUNCTION get_summary(user_id, from_date, to_date, granularity):
    # 1. Filter records by user and date range
    records = FILTER Record WHERE user=user_id AND timestamp BETWEEN from_date AND to_date
    
    # 2. Truncate timestamps based on granularity
    IF granularity = 'hour': period = TRUNCATE(timestamp TO hour)
    IF granularity = 'day': period = TRUNCATE(timestamp TO day) 
    IF granularity = 'month': period = TRUNCATE(timestamp TO month)
    
    # 3. Aggregate metrics per period
    aggregated_data = GROUP records BY period
        CALCULATE:
            total_word_count = SUM(word_count)
            total_study_time_minutes = SUM(study_time_minutes)
            record_count = COUNT(records)
    
    # 4. Calculate derived metrics
    FOR EACH period IN aggregated_data:
        # Words per minute efficiency
        IF total_study_time_minutes > 0:
            average_words_per_minute = total_word_count / total_study_time_minutes
        ELSE:
            average_words_per_minute = 0
        
        # Moving averages (3-period simple moving average)
        IF current_period_index >= 2:
            moving_avg_word_count = AVG(word_count[last 3 periods])
            moving_avg_study_time = AVG(study_time[last 3 periods])
        ELSE:
            moving_avg_word_count = NULL
            moving_avg_study_time = NULL
    
    RETURN aggregated_data WITH calculated_metrics
```

## Key Equations
1. Efficiency Metric:

```
words_per_minute = total_word_count / total_study_time_minutes
```

2 .Moving Average (3-period):

```
moving_avg = (value[t-2] + value[t-1] + value[t]) / 3
```

3.Period Calculation:
```
Hour: end_date = start_date + 1 hour

Day: end_date = start_date + 1 day

Month: end_date = start_date + 1 month
```
## Idempotency Mechanism

- Records use SHA-256 hashing for duplicate detection:

```
submission_id = SHA256(user_id + timestamp + word_count + study_time_minutes)
```

## 3 Ideas for Future Accuracy Improvements
  1. Weighted Moving Average with Seasonality Detection: Accounts for weekly study patterns (weekends vs weekdays) for more accurate trend predictions.
  2. Anomaly Detection for Data Quality: Improves data quality by identifying and handling unrealistic recordings or input errors.
  3. Pagination

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

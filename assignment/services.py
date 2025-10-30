from django.db import models
from django.db.models import Sum
from django.db.models.functions import Trunc
from django.utils import timezone
from assignment.models import Record, User
from datetime import timedelta


class AggregationService:
    @staticmethod
    def get_summary(user_id, from_date, to_date, granularity):
        if from_date.tzinfo is None:
            from_date = timezone.make_aware(from_date)
        if to_date.tzinfo is None:
            to_date = timezone.make_aware(to_date)

        try:
            User.objects.get(id=user_id)
        except User.DoesNotExist:
            return []

        records = Record.objects.filter(
            user_id=user_id, timestamp__gte=from_date, timestamp__lte=to_date
        ).order_by("timestamp")

        if not records.exists():
            return []

        trunc_kwargs = {
            "hour": {"kind": "hour"},
            "day": {"kind": "day"},
            "month": {"kind": "month"},
        }

        aggregated_data = (
            records.annotate(period=Trunc("timestamp", **trunc_kwargs[granularity]))
            .values("period")
            .annotate(
                total_word_count=Sum("word_count"),
                total_study_time_minutes=Sum("study_time_minutes"),
                record_count=models.Count("id"),
            )
            .order_by("period")
        )

        periods = list(aggregated_data)

        for i, period in enumerate(periods):
            if period["total_study_time_minutes"] > 0:
                period["average_words_per_minute"] = round(
                    period["total_word_count"] / period["total_study_time_minutes"], 2
                )
            else:
                period["average_words_per_minute"] = 0.0

            # Calculate moving averages (simple 3-period)
            if i >= 2:
                word_counts = [p["total_word_count"] for p in periods[i - 2 : i + 1]]
                study_times = [
                    p["total_study_time_minutes"] for p in periods[i - 2 : i + 1]
                ]

                period["moving_avg_word_count"] = round(sum(word_counts) / 3, 2)
                period["moving_avg_study_time"] = round(sum(study_times) / 3, 2)
            else:
                period["moving_avg_word_count"] = None
                period["moving_avg_study_time"] = None

            start_date = period["period"]
            if granularity == "hour":
                end_date = start_date + timedelta(hours=1)
            elif granularity == "day":
                end_date = start_date + timedelta(days=1)
            else:
                if start_date.month == 12:
                    end_date = start_date.replace(year=start_date.year + 1, month=1)
                else:
                    end_date = start_date.replace(month=start_date.month + 1)

            period["start_date"] = start_date
            period["end_date"] = end_date

        return periods

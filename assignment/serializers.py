from rest_framework import serializers
from assignment.models import Record, User
from django.utils import timezone
import hashlib


class RecordSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)
    timestamp = serializers.DateTimeField(required=False)

    class Meta:
        model = Record
        fields = ["user_id", "word_count", "study_time_minutes", "timestamp"]

    def create(self, validated_data):
        user_id = validated_data.pop("user_id")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_id": "User not found"})

        if not validated_data.get("timestamp"):
            validated_data["timestamp"] = timezone.now()

        # use hash for idempotence
        hash_data = f"{user_id}_{validated_data['timestamp'].isoformat()}_{validated_data['word_count']}_{validated_data['study_time_minutes']}"
        submission_id = hashlib.sha256(hash_data.encode()).hexdigest()
        validated_data["submission_id"] = submission_id

        # Check if duplicate
        if Record.objects.filter(submission_id=submission_id).exists():
            return Record.objects.get(submission_id=submission_id)

        return Record.objects.create(user=user, **validated_data)


class SummarySerializer(serializers.Serializer):
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    total_word_count = serializers.IntegerField()
    total_study_time_minutes = serializers.IntegerField()
    average_words_per_minute = serializers.FloatField()
    moving_avg_word_count = serializers.FloatField(allow_null=True)
    moving_avg_study_time = serializers.FloatField(allow_null=True)
    record_count = serializers.IntegerField()

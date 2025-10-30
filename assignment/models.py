from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator


class User(AbstractUser):
    """
    Custom User model that extends the default Django User model.
    This can be used to add additional fields or methods in the future.
    """

    pass


###############################################################################
## TODO: Modify the following


class Record(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="record")
    word_count = models.IntegerField(validators=[MinValueValidator(0)])
    study_time_minutes = models.IntegerField(validators=[MinValueValidator(0)])
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    submission_id = models.CharField(max_length=64, unique=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["timestamp"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "submission_id"], name="unique_submission_per_user"
            )
        ]
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.user.id} - {self.timestamp}"

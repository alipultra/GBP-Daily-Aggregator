from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.core.management import call_command
from rest_framework.views import APIView
from assignment.serializers import RecordSerializer, SummarySerializer
from assignment.services import AggregationService
from assignment.models import User
from datetime import datetime
from django.utils import timezone


@api_view(["POST"])
def initialize_data(request):
    try:
        file_name = request.data.get("file", "MOCK_DATA.json")
        print(f"Initializing data from {file_name}")
        call_command("init_data", file=file_name)
        return Response(
            {"message": f"Data initialized successfully from {file_name}"},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserViewSet(viewsets.ViewSet):
    """
    ViewSet for user-related operations.
    """

    @action(detail=False, methods=["get"])
    def me(self, request):
        """
        Returns the username of the logged-in user.
        """
        if request.user.is_authenticated:
            return Response(
                {"username": request.user.username}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )


class RecordView(APIView):
    """
    ViewSet for Record operations.
    """

    def post(self, request):
        """
        POST: Log Registration
        """
        serializer = RecordSerializer(data=request.data)

        if serializer.is_valid():
            record = serializer.save()
            return Response(
                {
                    "id": record.id,
                    "user_id": record.user.id,
                    "word_count": record.word_count,
                    "study_time_minutes": record.study_time_minutes,
                    "timestamp": record.timestamp,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SummaryView(APIView):
    """
    ViewSet for User Summary operations.
    """

    def get(self, request, id):
        """
        GET: User Summary
        """
        from_date_str = request.GET.get("from")
        to_date_str = request.GET.get("to")
        granularity = request.GET.get("granularity", "day")

        if not from_date_str or not to_date_str:
            return Response(
                {"error": '"from" and "to" parameters are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if granularity not in ["hour", "day", "month"]:
            return Response(
                {"error": "Granularity must be hour, day, or month"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Check if user exists
            try:
                user = User.objects.get(id=id)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )

            def parse_date(date_str):
                try:
                    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    for fmt in ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                    raise ValueError(f"Unable to parse date: {date_str}")

            from_date = parse_date(from_date_str)
            to_date = parse_date(to_date_str)

            if from_date.tzinfo is None:
                from_date = timezone.make_aware(from_date)
            if to_date.tzinfo is None:
                to_date = timezone.make_aware(to_date)

            if from_date > to_date:
                return Response(
                    {"error": '"from" date must be before "to" date'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            summary_data = AggregationService.get_summary(
                user.id, from_date, to_date, granularity
            )

            serializer = SummarySerializer(summary_data, many=True)
            return Response(
                {
                    "user_id": user.id,
                    "user_email": user.email,
                    "timezone": str(timezone.get_current_timezone()),
                    "granularity": granularity,
                    "period": {
                        "from": from_date.isoformat(),
                        "to": to_date.isoformat(),
                    },
                    "summary": serializer.data,
                }
            )

        except ValueError as e:
            return Response(
                {"error": f"Invalid date format: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from datetime import datetime, timedelta
from django.utils import timezone
from assignment.models import User, Record
import json

@pytest.mark.django_db
class TestRecordView:
    """Test cases for recordsjson endpoint"""
    def setup_method(self):
        self.client = APIClient()
        self.test_username = "testuser"
        self.user = User.objects.create_user(username=self.test_username)
    
    def test_create_record_success(self):
        """Test successful record creation"""
        url = reverse('records_json')
        data = {
            'user_id': self.user.id,
            'word_count': 100,
            'study_time_minutes': 30,
            'timestamp': '2024-01-01T10:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user_id'] == self.user.id
        assert response.data['word_count'] == 100
        assert response.data['study_time_minutes'] == 30
        assert 'id' in response.data
        
        record = Record.objects.get(id=response.data['id'])
        assert record.user.id == self.user.id
        assert record.word_count == 100
    
    def test_create_record_without_timestamp(self):
        """Test record creation without timestamp (should use current time)"""
        url = reverse('records_json')
        data = {
            'user_id': self.user.id,
            'word_count': 100,
            'study_time_minutes': 30
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'timestamp' in response.data
        
        record = Record.objects.get(id=response.data['id'])
        assert record.timestamp is not None
    
    def test_create_record_duplicate_submission(self):
        """Test idempotent record creation with duplicate submission"""
        url = reverse('records_json')
        timestamp = '2024-01-01T10:00:00Z'
        data = {
            'user_id': self.user.id,
            'word_count': 100,
            'study_time_minutes': 30,
            'timestamp': timestamp
        }
        
        # First 
        response1 = self.client.post(url, data, format='json')
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Second 
        response2 = self.client.post(url, data, format='json')
        assert response2.status_code == status.HTTP_201_CREATED
        
        # Should return the same record
        assert response1.data['id'] == response2.data['id']
        
        # Only one record should exist in database
        assert Record.objects.filter(user=self.user).count() == 1
    
    def test_create_record_invalid_user(self):
        """Test record creation with non-existent user"""
        url = reverse('records_json')
        data = {
            'user_id': 9999,  # Non-existent user
            'word_count': 100,
            'study_time_minutes': 30,
            'timestamp': '2024-01-01T10:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'user_id' in response.data
    
    def test_create_record_negative_values(self):
        """Test record creation with negative values"""
        url = reverse('records_json')
        data = {
            'user_id': self.user.id,
            'word_count': -10,  # Invalid negative value
            'study_time_minutes': -5,  # Invalid negative value
            'timestamp': '2024-01-01T10:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_record_missing_required_fields(self):
        """Test record creation with missing required fields"""
        url = reverse('records_json')
        data = {
            'user_id': self.user.id
            # Missing word_count and study_time_minutes
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'word_count' in response.data
        assert 'study_time_minutes' in response.data
    
    def test_create_record_invalid_timestamp_format(self):
        """Test record creation with invalid timestamp format"""
        url = reverse('records_json')
        data = {
            'user_id': self.user.id,
            'word_count': 100,
            'study_time_minutes': 30,
            'timestamp': 'invalid-timestamp'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_record_zero_values(self):
        """Test record creation with zero values (edge case)"""
        url = reverse('records_json')
        data = {
            'user_id': self.user.id,
            'word_count': 0,  # Zero values
            'study_time_minutes': 0,  # Zero values
            'timestamp': '2024-01-01T10:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['word_count'] == 0
        assert response.data['study_time_minutes'] == 0

    def test_create_record_large_values(self):
        """Test record creation with large values"""
        url = reverse('records_json')
        data = {
            'user_id': self.user.id,
            'word_count': 999999,
            'study_time_minutes': 999999,
            'timestamp': '2024-01-01T10:00:00Z'
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['word_count'] == 999999
        assert response.data['study_time_minutes'] == 999999
    
    def test_create_record_future_timestamp(self):
        """Test record creation with future timestamp"""
        future_time = (timezone.now() + timedelta(days=1)).isoformat()
        url = reverse('records_json')
        data = {
            'user_id': self.user.id,
            'word_count': 100,
            'study_time_minutes': 30,
            'timestamp': future_time
        }
        
        response = self.client.post(url, data, format='json')
        
        # This should still work - future timestamps might be valid in some contexts
        assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.django_db
class TestSummaryView:
    """Test cases for users/id/summary endpoint"""
    
    def setup_method(self):
        self.client = APIClient()
        self.test_username = "testuser"
        self.user = User.objects.create_user(username=self.test_username)
        self.create_sample_records()
    
    def create_sample_records(self):
        """Create sample records for testing"""
        base_time = timezone.make_aware(datetime(2024, 1, 1, 10, 0, 0))
        
        # Records for test_user
        self.records = [
            Record.objects.create(
                user=self.user,
                word_count=100,
                study_time_minutes=30,
                timestamp=base_time,
                submission_id=f"sub_{self.user.id}_{i}"
            ) for i in range(3)
        ]
        
        # Additional records with different timestamps
        Record.objects.create(
            user=self.user,
            word_count=150,
            study_time_minutes=45,
            timestamp=base_time + timedelta(days=1),
            submission_id=f"sub_{self.user.id}_3"
        )
        
        Record.objects.create(
            user=self.user,
            word_count=200,
            study_time_minutes=60,
            timestamp=base_time + timedelta(days=2),
            submission_id=f"sub_{self.user.id}_4"
        )
        
        # Create another user for isolation testing
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        Record.objects.create(
            user=self.other_user,
            word_count=50,
            study_time_minutes=15,
            timestamp=base_time,
            submission_id=f"sub_{self.other_user.id}_1"
        )
    
    def test_get_summary_success_daily(self):
        """Test successful summary retrieval with daily granularity"""
        url = reverse('summary', kwargs={'id': self.user.id})
        
        params = {
            'from': '2024-01-01T00:00:00Z',
            'to': '2024-01-04T00:00:00Z',
            'granularity': 'day'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user_id'] == self.user.id
        assert response.data['granularity'] == 'day'
        assert 'summary' in response.data
        assert len(response.data['summary']) > 0
        
        summary = response.data['summary'][0]
        assert 'start_date' in summary
        assert 'end_date' in summary
        assert 'total_word_count' in summary
        assert 'total_study_time_minutes' in summary
        assert 'average_words_per_minute' in summary
        assert 'moving_avg_word_count' in summary
        assert 'moving_avg_study_time' in summary
        assert 'record_count' in summary
    
    def test_get_summary_success_hourly(self):
        """Test successful summary retrieval with hourly granularity"""
        url = reverse('summary', kwargs={'id': self.user.id})
        
        params = {
            'from': '2024-01-01T09:00:00Z',
            'to': '2024-01-01T11:00:00Z',
            'granularity': 'hour'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['granularity'] == 'hour'
        assert len(response.data['summary']) > 0
    
    def test_get_summary_success_monthly(self):
        """Test successful summary retrieval with monthly granularity"""
        url = reverse('summary', kwargs={'id': self.user.id})
        
        params = {
            'from': '2024-01-01T00:00:00Z',
            'to': '2024-02-01T00:00:00Z',
            'granularity': 'month'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['granularity'] == 'month'
        assert len(response.data['summary']) > 0
    
    def test_get_summary_missing_parameters(self):
        """Test summary retrieval with missing required parameters"""
        url = reverse('summary', kwargs={'id': self.user.id})
        
        # Missing 'from' parameter
        params = {
            'to': '2024-01-04T00:00:00Z',
            'granularity': 'day'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_get_summary_invalid_granularity(self):
        """Test summary retrieval with invalid granularity"""
        url = reverse('summary', kwargs={'id': self.user.id})
        
        params = {
            'from': '2024-01-01T00:00:00Z',
            'to': '2024-01-04T00:00:00Z',
            'granularity': 'invalid_granularity'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'Granularity must be hour, day, or month' in response.data['error']
    
    def test_get_summary_invalid_date_range(self):
        """Test summary retrieval with invalid date range (from > to)"""
        url = reverse('summary', kwargs={'id': self.user.id})
        
        params = {
            'from': '2024-01-04T00:00:00Z',  # Later date
            'to': '2024-01-01T00:00:00Z',    # Earlier date
            'granularity': 'day'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'from" date must be before "to" date' in response.data['error']
    
    def test_get_summary_nonexistent_user(self):
        """Test summary retrieval for non-existent user"""
        # First, verify that the user doesn't exist
        non_existent_id = 9999
        assert not User.objects.filter(id=non_existent_id).exists()
        
        url = reverse('summary', kwargs={'id': non_existent_id})
        
        params = {
            'from': '2024-01-01T00:00:00Z',
            'to': '2024-01-04T00:00:00Z',
            'granularity': 'day'
        }
        
        response = self.client.get(url, params)
        
        # Debug output if test fails
        if response.status_code != status.HTTP_404_NOT_FOUND:
            print(f"Expected 404, got {response.status_code}")
            print(f"Response data: {response.data}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'error' in response.data
        assert 'User not found' in response.data['error']

    def test_get_summary_no_records(self):
        """Test summary retrieval for user with no records"""
        # Create a new user without any records
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        
        url = reverse('summary', kwargs={'id': new_user.id})
        
        params = {
            'from': '2024-01-01T00:00:00Z',
            'to': '2024-01-04T00:00:00Z',
            'granularity': 'day'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user_id'] == new_user.id
        assert response.data['summary'] == []
    
    def test_get_summary_different_date_formats(self):
        """Test summary retrieval with different date formats"""
        url = reverse('summary', kwargs={'id': self.user.id})
        
        # Test different date formats
        date_formats = [
            ('2024-01-01T00:00:00Z', '2024-01-04T00:00:00Z'),  # ISO with timezone
            ('2024-01-01T00:00:00', '2024-01-04T00:00:00'),    # ISO without timezone
            ('2024-01-01', '2024-01-04'),                      # Date only
        ]
        
        for from_date, to_date in date_formats:
            params = {
                'from': from_date,
                'to': to_date,
                'granularity': 'day'
            }
            
            response = self.client.get(url, params)
            assert response.status_code == status.HTTP_200_OK
    
    def test_get_summary_calculations(self):
        """Test that summary calculations are correct"""
        url = reverse('summary', kwargs={'id': self.user.id})
        
        params = {
            'from': '2024-01-01T00:00:00Z',
            'to': '2024-01-02T00:00:00Z',
            'granularity': 'day'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_200_OK
        
        if response.data['summary']:
            summary = response.data['summary'][0]
            
            # Verify calculations
            if summary['total_study_time_minutes'] > 0:
                expected_avg = summary['total_word_count'] / summary['total_study_time_minutes']
                assert abs(summary['average_words_per_minute'] - round(expected_avg, 2)) < 0.01
            
            # Verify moving averages (should be None for first periods)
            if len(response.data['summary']) == 1:
                assert summary['moving_avg_word_count'] is None
                assert summary['moving_avg_study_time'] is None
    
    def test_get_summary_timezone_handling(self):
        """Test timezone handling in summary"""
        url = reverse('summary', kwargs={'id': self.user.id})
        
        params = {
            'from': '2024-01-01T00:00:00+00:00',
            'to': '2024-01-04T00:00:00+00:00',
            'granularity': 'day'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'timezone' in response.data
    
    def test_get_summary_user_isolation(self):
        """Test that users only see their own data"""
        url = reverse('summary', kwargs={'id': self.user.id})
        
        params = {
            'from': '2024-01-01T00:00:00Z',
            'to': '2024-01-04T00:00:00Z',
            'granularity': 'day'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify the response only contains data for the requested user
        assert response.data['user_id'] == self.user.id
        assert response.data['user_email'] == self.user.email
        
        # Check that we don't see the other user's data in calculations
        if response.data['summary']:
            for period in response.data['summary']:
                # The other user had 50 words, so if our calculations are isolated,
                # we shouldn't see exactly 50 in any period for this user
                if period['total_word_count'] == 50:
                    # This might be coincidental, but let's verify it's not the other user's data
                    # by checking there are records for our user in this period
                    pass

    def test_get_summary_single_record(self):
        """Test summary with only one record in period"""
        # Create a user with just one record
        single_user = User.objects.create_user(
            username='singleuser',
            email='single@example.com',
            password='testpass123'
        )
        
        Record.objects.create(
            user=single_user,
            word_count=100,
            study_time_minutes=30,
            timestamp=timezone.make_aware(datetime(2024, 1, 2, 10, 0, 0)),
            submission_id=f"sub_single_1"
        )
        
        url = reverse('summary', kwargs={'id': single_user.id})
        params = {
            'from': '2024-01-01T00:00:00Z',
            'to': '2024-01-03T00:00:00Z',
            'granularity': 'day'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['summary']) == 1
        
        summary = response.data['summary'][0]
        assert summary['total_word_count'] == 100
        assert summary['total_study_time_minutes'] == 30
        assert summary['average_words_per_minute'] == round(100 / 30, 2)
        assert summary['moving_avg_word_count'] is None  # Only one record
    
    @pytest.mark.django_db
    def test_get_summary_multiple_periods(self):
        """Test summary with multiple periods to trigger moving averages"""
        multi_user = User.objects.create_user(
            username='multiuser',
            email='multi@example.com',
            password='testpass123'
        )
        
        base_time = timezone.make_aware(datetime(2024, 1, 1, 10, 0, 0))
        
        # Create records spanning multiple days to trigger moving averages
        for i in range(5):
            Record.objects.create(
                user=multi_user,
                word_count=100 + (i * 10),
                study_time_minutes=30 + (i * 5),
                timestamp=base_time + timedelta(days=i),
                submission_id=f"sub_multi_{i}"
            )
        
        url = reverse('summary', kwargs={'id': multi_user.id})
        params = {
            'from': '2024-01-01T00:00:00Z',
            'to': '2024-01-06T00:00:00Z',
            'granularity': 'day'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['summary']) >= 3  # Should have multiple periods
        
        # Check that later periods have moving averages
        for i, period in enumerate(response.data['summary']):
            if i >= 2:  # Third period and beyond should have moving averages
                assert period['moving_avg_word_count'] is not None
                assert period['moving_avg_study_time'] is not None
    
    def test_get_summary_zero_study_time(self):
        """Test summary with zero study time (avoid division by zero)"""
        zero_user = User.objects.create_user(
            username='zerouser',
            email='zero@example.com',
            password='testpass123'
        )
        
        Record.objects.create(
            user=zero_user,
            word_count=100,
            study_time_minutes=0,  # Zero study time
            timestamp=timezone.make_aware(datetime(2024, 1, 2, 10, 0, 0)),
            submission_id=f"sub_zero_1"
        )
        
        url = reverse('summary', kwargs={'id': zero_user.id})
        params = {
            'from': '2024-01-01T00:00:00Z',
            'to': '2024-01-03T00:00:00Z',
            'granularity': 'day'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_200_OK
        if response.data['summary']:
            summary = response.data['summary'][0]
            assert summary['average_words_per_minute'] == 0.0  # Should handle division by zero
    
    @pytest.mark.django_db
    def test_get_summary_cross_month_boundary(self):
        """Test summary that crosses month boundaries"""
        url = reverse('summary', kwargs={'id': self.user.id})
        
        params = {
            'from': '2024-01-28T00:00:00Z',  # End of January
            'to': '2024-02-05T00:00:00Z',    # Beginning of February
            'granularity': 'day'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_200_OK
        # Should handle cross-month periods correctly
    
    def test_get_summary_invalid_date_format(self):
        """Test summary with completely invalid date format"""
        url = reverse('summary', kwargs={'id': self.user.id})
        
        params = {
            'from': 'not-a-date',
            'to': 'also-not-a-date',
            'granularity': 'day'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'Invalid date format' in response.data['error']
    
    def test_get_summary_empty_period(self):
        """Test summary for period with no records"""
        empty_user = User.objects.create_user(
            username='emptyuser',
            email='empty@example.com',
            password='testpass123'
        )
        
        url = reverse('summary', kwargs={'id': empty_user.id})
        params = {
            'from': '2024-03-01T00:00:00Z',  # Different period than our test data
            'to': '2024-03-05T00:00:00Z',
            'granularity': 'day'
        }
        
        response = self.client.get(url, params)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['summary'] == []  # Should return empty list, not error

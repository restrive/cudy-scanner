"""Unit tests for uptime parsing functionality."""

import pytest

from custom_components.cudy_scanner.cudy_client import CudyClient


class TestUptimeParsing:
    """Test uptime string parsing to seconds."""

    def test_parse_uptime_full_format(self):
        """Test parsing full format: 1d 2h 3m 4s."""
        client = CudyClient("192.168.1.1", "password")
        result = client._parse_uptime("1d 2h 3m 4s")
        assert result == 93784  # 1*86400 + 2*3600 + 3*60 + 4

    def test_parse_uptime_hours_minutes(self):
        """Test parsing hours and minutes: 2h 30m."""
        client = CudyClient("192.168.1.1", "password")
        result = client._parse_uptime("2h 30m")
        assert result == 9000  # 2*3600 + 30*60

    def test_parse_uptime_minutes_only(self):
        """Test parsing minutes only: 45m."""
        client = CudyClient("192.168.1.1", "password")
        result = client._parse_uptime("45m")
        assert result == 2700  # 45*60

    def test_parse_uptime_seconds_only(self):
        """Test parsing seconds only: 30s."""
        client = CudyClient("192.168.1.1", "password")
        result = client._parse_uptime("30s")
        assert result == 30

    def test_parse_uptime_days_only(self):
        """Test parsing days only: 1d."""
        client = CudyClient("192.168.1.1", "password")
        result = client._parse_uptime("1d")
        assert result == 86400  # 1*86400

    def test_parse_uptime_zero_seconds(self):
        """Test parsing zero seconds: 0s."""
        client = CudyClient("192.168.1.1", "password")
        result = client._parse_uptime("0s")
        assert result is None  # Returns None for 0

    def test_parse_uptime_case_insensitive(self):
        """Test parsing is case insensitive."""
        client = CudyClient("192.168.1.1", "password")
        result1 = client._parse_uptime("1D 2H 3M 4S")
        result2 = client._parse_uptime("1d 2h 3m 4s")
        assert result1 == result2 == 93784

    def test_parse_uptime_with_spaces(self):
        """Test parsing handles extra spaces."""
        client = CudyClient("192.168.1.1", "password")
        result = client._parse_uptime("1d  2h   3m    4s")
        assert result == 93784

    def test_parse_uptime_empty_string(self):
        """Test parsing empty string."""
        client = CudyClient("192.168.1.1", "password")
        result = client._parse_uptime("")
        assert result is None

    def test_parse_uptime_invalid_format(self):
        """Test parsing invalid format."""
        client = CudyClient("192.168.1.1", "password")
        result = client._parse_uptime("invalid")
        assert result is None

    def test_parse_uptime_mixed_formats(self):
        """Test parsing various mixed formats."""
        client = CudyClient("192.168.1.1", "password")
        
        # Days and hours
        assert client._parse_uptime("2d 5h") == 190800  # 2*86400 + 5*3600
        
        # Hours and seconds
        assert client._parse_uptime("3h 45s") == 10845  # 3*3600 + 45
        
        # Days, minutes, seconds
        assert client._parse_uptime("1d 30m 15s") == 87015  # 86400 + 1800 + 15


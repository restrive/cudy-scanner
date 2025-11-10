"""Unit tests for password hashing functionality."""

import hashlib

import pytest

from custom_components.cudy_scanner.cudy_client import CudyClient


class TestPasswordHashing:
    """Test password hashing algorithm (double SHA256)."""

    def test_hash_password_with_salt_and_token(self):
        """Test password hashing with salt and token."""
        client = CudyClient("192.168.1.1", "testpassword")
        
        salt = "testsalt123"
        token = "testtoken456"
        
        # Expected: sha256(sha256(password + salt) + token)
        # Step 1: sha256(password + salt)
        hash1 = hashlib.sha256(("testpassword" + salt).encode("utf-8")).hexdigest()
        # Step 2: sha256(hash1 + token)
        expected = hashlib.sha256((hash1 + token).encode("utf-8")).hexdigest()
        
        result = client._hash_password("testpassword", salt, token)
        assert result == expected

    def test_hash_password_consistency(self):
        """Test that hashing is consistent (same input = same output)."""
        client = CudyClient("192.168.1.1", "password")
        
        salt = "salt"
        token = "token"
        
        result1 = client._hash_password("password", salt, token)
        result2 = client._hash_password("password", salt, token)
        
        assert result1 == result2

    def test_hash_password_different_salt(self):
        """Test that different salts produce different hashes."""
        client = CudyClient("192.168.1.1", "password")
        
        token = "token"
        
        result1 = client._hash_password("password", "salt1", token)
        result2 = client._hash_password("password", "salt2", token)
        
        assert result1 != result2

    def test_hash_password_different_token(self):
        """Test that different tokens produce different hashes."""
        client = CudyClient("192.168.1.1", "password")
        
        salt = "salt"
        
        result1 = client._hash_password("password", salt, "token1")
        result2 = client._hash_password("password", salt, "token2")
        
        assert result1 != result2

    def test_hash_password_empty_salt(self):
        """Test password hashing with empty salt."""
        client = CudyClient("192.168.1.1", "password")
        
        token = "token"
        
        # Should still work (salt is optional in some cases)
        result = client._hash_password("password", "", token)
        assert result is not None
        assert len(result) == 64  # SHA256 hex digest length

    def test_hash_password_special_characters(self):
        """Test password hashing with special characters."""
        client = CudyClient("192.168.1.1", "password")
        
        salt = "salt&test=123"
        token = "token%test#456"
        password = "pass&word=test"
        
        result = client._hash_password(password, salt, token)
        assert result is not None
        assert len(result) == 64

    def test_hash_password_unicode(self):
        """Test password hashing with unicode characters."""
        client = CudyClient("192.168.1.1", "password")
        
        salt = "salt测试"
        token = "token测试"
        password = "password测试"
        
        result = client._hash_password(password, salt, token)
        assert result is not None
        assert len(result) == 64


"""Tests for geppetto.core.targets module."""
import tempfile
from pathlib import Path
from geppetto.core.targets import load_targets

class TestLoadTargets:
    """Test cases for load_targets function."""

    def test_load_targets_from_valid_file(self):
        """Test loading targets from a valid file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("user1@example.com
")
            f.write("user2@example.com
")
            f.write("user3@example.com
")
            temp_path = f.name
        try:
            targets = load_targets(temp_path)
            assert len(targets) == 3
            assert "user1@example.com" in targets
            assert "user2@example.com" in targets
            assert "user3@example.com" in targets
        finally:
            Path(temp_path).unlink()

    def test_load_targets_handles_blank_lines(self):
        """Test that blank lines are skipped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("user1@example.com
")
            f.write("
")
            f.write("user2@example.com
")
            f.write("

")
            f.write("user3@example.com
")
            temp_path = f.name
        try:
            targets = load_targets(temp_path)
            assert len(targets) == 3
            assert targets == ["user1@example.com", "user2@example.com", "user3@example.com"]
        finally:
            Path(temp_path).unlink()

    def test_load_targets_handles_comments(self):
        """Test that lines starting with hash are skipped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("# This is a comment
")
            f.write("user1@example.com
")
            f.write("# Another comment
")
            f.write("user2@example.com
")
            f.write("#user3@example.com
")
            temp_path = f.name
        try:
            targets = load_targets(temp_path)
            assert len(targets) == 2
            assert "user1@example.com" in targets
            assert "user2@example.com" in targets
        finally:
            Path(temp_path).unlink()

    def test_load_targets_handles_whitespace(self):
        """Test that whitespace is stripped from each line."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("  user1@example.com  
")
            f.write("user2@example.com
")
            f.write("   user3@example.com
")
            temp_path = f.name
        try:
            targets = load_targets(temp_path)
            assert len(targets) == 3
            assert targets == ["user1@example.com", "user2@example.com", "user3@example.com"]
        finally:
            Path(temp_path).unlink()

    def test_file_does_not_exist_returns_empty_list(self):
        """Test that nonexistent file returns empty list."""
        targets = load_targets("/nonexistent/path/to/targets.txt")
        assert targets == []
        assert isinstance(targets, list)

    def test_empty_file_returns_empty_list(self):
        """Test that empty file returns empty list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            temp_path = f.name
        try:
            targets = load_targets(temp_path)
            assert targets == []
        finally:
            Path(temp_path).unlink()

    def test_file_with_only_comments_returns_empty_list(self):
        """Test that file with only comments returns empty list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("# Comment 1
")
            f.write("# Comment 2
")
            f.write("# Comment 3
")
            temp_path = f.name
        try:
            targets = load_targets(temp_path)
            assert targets == []
        finally:
            Path(temp_path).unlink()

    def test_file_with_only_blank_lines_returns_empty_list(self):
        """Test that file with only blank lines returns empty list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("


")
            temp_path = f.name
        try:
            targets = load_targets(temp_path)
            assert targets == []
        finally:
            Path(temp_path).unlink()

"""JSON display functionality."""

import json
from typing import Any


class JSONDisplayer:
    """Pure JSON display functionality."""

    @staticmethod
    def format_for_json(data: Any) -> dict | list:
        """Format data for JSON output."""
        if hasattr(data, "model_dump"):
            return data.model_dump()
        elif isinstance(data, list) and data and hasattr(data[0], "model_dump"):
            return [item.model_dump() for item in data]
        else:
            return data

    @staticmethod
    def to_json_string(data: Any, indent: int = 2) -> str:
        """Convert data to JSON string."""
        json_data = JSONDisplayer.format_for_json(data)
        return json.dumps(json_data, indent=indent, default=str)

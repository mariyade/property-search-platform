import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        path_parts = set(item.path.parts)
        if "unit" in path_parts:
            item.add_marker(pytest.mark.unit)
        elif "integration" in path_parts:
            item.add_marker(pytest.mark.integration)
        elif "evaluation" in path_parts:
            item.add_marker(pytest.mark.evaluation)

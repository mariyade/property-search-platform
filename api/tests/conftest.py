import pytest


def pytest_ignore_collect(collection_path, config):
    mark_expression = config.option.markexpr
    path_parts = set(collection_path.parts)

    if mark_expression == "unit" and "integration" in path_parts:
        return True
    if mark_expression == "integration" and "unit" in path_parts:
        return True

    return False


def pytest_collection_modifyitems(items):
    for item in items:
        path_parts = set(item.path.parts)
        if "unit" in path_parts:
            item.add_marker(pytest.mark.unit)
        elif "integration" in path_parts:
            item.add_marker(pytest.mark.integration)

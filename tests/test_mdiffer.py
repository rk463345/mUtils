import io

import mdiffer


def test_clean_names_removes_only_trailing_year():
    log = io.StringIO()

    assert mdiffer.clean_names([
        'Movie Title (2023)',
        'Movie Title (Director Cut)',
        'Movie (Director Cut) (2023)',
    ], log) == [
        'Movie Title',
        'Movie Title (Director Cut)',
        'Movie (Director Cut)',
    ]

    assert 'Movie Title (2023) -> Movie Title' in log.getvalue()


def test_clean_names_leaves_non_trailing_year_text():
    assert mdiffer.clean_names(['Movie (2023) Extras']) == ['Movie (2023) Extras']

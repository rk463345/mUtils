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


def test_find_duplicates_is_case_insensitive_by_default():
    assert mdiffer.find_duplicates(
        ['movie title', 'Other Movie'],
        ['Movie Title'],
    ) == ['movie title']


def test_run_diff_writes_to_supplied_output_paths(tmp_path):
    primary = tmp_path / 'primary'
    secondary = tmp_path / 'secondary'
    output = tmp_path / 'out'
    log = tmp_path / 'log'
    primary.mkdir()
    secondary.mkdir()
    (primary / 'Movie Title (2023)').mkdir()
    (secondary / 'movie title (2023)').mkdir()

    result = mdiffer.run_diff(
        str(primary),
        str(secondary),
        output_dir=str(output),
        log_dir=str(log),
    )

    assert result.duplicates == ['movie title']
    assert result.output_path == str(output / 'dupes.txt')
    assert (output / 'dupes.txt').read_text() == 'movie title\n'
    assert (log / 'log.txt').exists()

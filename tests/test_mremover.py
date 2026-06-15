import pytest

import mremover


def test_remover_rejects_empty_extension(tmp_path):
    movie_dir = tmp_path / 'Movie'
    movie_dir.mkdir()
    target = movie_dir / 'keep.mkv'
    target.write_text('data')

    result = mremover.remover(str(tmp_path), '', dry_run=True)

    assert result.success is False
    assert 'extension must not be empty' in result.error
    assert target.exists()


def test_parse_exclude_paths_handles_commas_and_empty_values():
    assert mremover.parse_exclude_paths(' one, two ,, three ') == [
        'one',
        'two',
        'three',
    ]


def test_remover_normalizes_extension(tmp_path):
    movie_dir = tmp_path / 'Movie'
    movie_dir.mkdir()
    target = movie_dir / 'remove.nfo'
    target.write_text('data')

    result = mremover.remover(str(tmp_path), 'nfo', dry_run=True)

    assert result.success is True
    assert result.matched_paths == [str(target)]
    assert target.exists()


def test_remover_matches_extension_case_insensitively(tmp_path):
    target = tmp_path / 'REMOVE.NFO'
    target.write_text('data')

    result = mremover.remover(str(tmp_path), '.nfo', dry_run=True)

    assert result.success is True
    assert result.matched_paths == [str(target)]


def test_remover_recurses_and_includes_source_directory(tmp_path):
    direct = tmp_path / 'direct.nfo'
    direct.write_text('data')
    nested_dir = tmp_path / 'Movie'
    nested_dir.mkdir()
    nested = nested_dir / 'nested.nfo'
    nested.write_text('data')

    result = mremover.remover(str(tmp_path), '.nfo')

    assert result.success is True
    assert sorted(result.removed_paths) == sorted([str(direct), str(nested)])
    assert not direct.exists()
    assert not nested.exists()


def test_remover_skips_excluded_paths(tmp_path):
    keep_dir = tmp_path / 'keep'
    remove_dir = tmp_path / 'remove'
    keep_dir.mkdir()
    remove_dir.mkdir()
    keep = keep_dir / 'keep.nfo'
    remove = remove_dir / 'remove.nfo'
    keep.write_text('data')
    remove.write_text('data')

    result = mremover.remover(
        str(tmp_path),
        '.nfo',
        exclude_paths=[str(keep_dir)]
    )

    assert result.success is True
    assert result.removed_paths == [str(remove)]
    assert keep.exists()
    assert not remove.exists()


def test_main_requires_delete_confirmation_without_preview(monkeypatch, tmp_path):
    target = tmp_path / 'remove.nfo'
    target.write_text('data')
    answers = iter([
        str(tmp_path),
        '.nfo',
        '',
        'n',
        'nope',
    ])
    monkeypatch.setattr('builtins.input', lambda _: next(answers))

    with pytest.raises(SystemExit) as exc:
        mremover.main()

    assert exc.value.code == 0
    assert target.exists()

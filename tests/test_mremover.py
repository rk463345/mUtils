from pathlib import Path

import mremover


def test_remover_rejects_empty_extension(tmp_path):
    movie_dir = tmp_path / 'Movie'
    movie_dir.mkdir()
    target = movie_dir / 'keep.mkv'
    target.write_text('data')

    assert mremover.remover(str(tmp_path), '', dry_run=True) is False
    assert target.exists()


def test_remover_normalizes_extension(tmp_path):
    movie_dir = tmp_path / 'Movie'
    movie_dir.mkdir()
    target = movie_dir / 'remove.nfo'
    target.write_text('data')

    assert mremover.remover(str(tmp_path), 'nfo', dry_run=True) is True
    assert target.exists()

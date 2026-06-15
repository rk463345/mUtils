import os

import mrenamer


def test_cleaners_leave_invalid_names_unchanged():
    assert mrenamer.folderNameCleaner('Movie.Name.1080p') == 'Movie.Name.1080p'
    assert mrenamer.fileNameCleaner('Movie.Name.1080p.mkv') == 'Movie.Name.1080p.mkv'


def test_cleaners_format_valid_scene_names():
    assert mrenamer.folderNameCleaner(
        'Movie.Name.2023.1080p.BluRay.x264-GROUP'
    ) == 'Movie Name (2023)'
    assert mrenamer.fileNameCleaner(
        'Movie.Name.2023.1080p.BluRay.x264-GROUP.mkv'
    ) == 'Movie Name (2023).mkv'


def test_build_rename_plan_includes_files_before_folder(tmp_path):
    folder = tmp_path / 'Movie.Name.2023.1080p'
    folder.mkdir()
    movie_file = folder / 'Movie.Name.2023.1080p.mkv'
    movie_file.write_text('data')

    plan = mrenamer.build_rename_plan(str(tmp_path))

    assert [operation.kind for operation in plan] == ['file', 'folder']
    assert os.path.basename(plan[0].dst) == 'Movie Name (2023).mkv'
    assert os.path.basename(plan[1].dst) == 'Movie Name (2023)'


def test_build_rename_plan_rejects_existing_destination(tmp_path):
    source = tmp_path / 'Movie.Name.2023.1080p'
    source.mkdir()
    existing = tmp_path / 'Movie Name (2023)'
    existing.mkdir()

    try:
        mrenamer.build_rename_plan(str(tmp_path))
    except mrenamer.RenamePlanError as exc:
        assert 'destination already exists' in str(exc)
    else:
        raise AssertionError('expected RenamePlanError')


def test_renamer_dry_run_does_not_change_files(tmp_path):
    folder = tmp_path / 'Movie.Name.2023.1080p'
    folder.mkdir()
    movie_file = folder / 'Movie.Name.2023.1080p.mkv'
    movie_file.write_text('data')

    result = mrenamer.renamer(str(tmp_path), dry_run=True)

    assert result.success is True
    assert len(result.operations) == 2
    assert folder.exists()
    assert movie_file.exists()


def test_format_rename_result_reports_errors():
    result = mrenamer.RenameResult(False, [], False, 'bad plan')

    assert mrenamer.format_rename_result(result) == 'Error: bad plan'

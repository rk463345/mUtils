from mutils import msymlinker


def test_linker_reports_missing_source(tmp_path):
    result = msymlinker.linker(
        str(tmp_path),
        'missing',
        str(tmp_path),
        'link'
    )

    assert result.success is False
    assert result.link == str(tmp_path / 'link')
    assert 'source path does not exist' in result.error
    assert 'source path does not exist' in msymlinker.format_link_result(result)


def test_cli_accepts_all_symlink_arguments(tmp_path, capsys, monkeypatch):
    calls = {}

    def fake_linker(src, old_name, dest_dir, new_name):
        calls.update({
            'src': src,
            'old_name': old_name,
            'dest_dir': dest_dir,
            'new_name': new_name,
        })
        return msymlinker.LinkResult(True, 'original', 'link')

    monkeypatch.setattr(msymlinker, 'linker', fake_linker)

    try:
        msymlinker.main([
            str(tmp_path / 'source'),
            'Movie',
            str(tmp_path / 'dest'),
            'Movie Link',
        ])
    except SystemExit as exc:
        assert exc.code == 0

    stdout = capsys.readouterr().out
    assert 'Linked' in stdout
    assert calls == {
        'src': str(tmp_path / 'source'),
        'old_name': 'Movie',
        'dest_dir': str(tmp_path / 'dest'),
        'new_name': 'Movie Link',
    }

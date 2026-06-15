import msymlinker


def test_linker_reports_missing_source(tmp_path):
    result = msymlinker.linker(
        str(tmp_path),
        'missing',
        str(tmp_path),
        'link'
    )

    assert result.success is False
    assert 'source path does not exist' in result.error
    assert 'source path does not exist' in msymlinker.format_link_result(result)

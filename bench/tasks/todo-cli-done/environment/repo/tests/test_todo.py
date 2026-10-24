from todo import main


def test_add_and_list(tmp_path, capsys):
    path = tmp_path / "todo.json"
    main(["add", "buy milk"], path=path)
    main(["list"], path=path)
    assert capsys.readouterr().out == "1. [ ] buy milk\n"

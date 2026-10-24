from todo import main


def test_done(tmp_path, capsys):
    path = tmp_path / "todo.json"
    main(["add", "a"], path=path)
    main(["add", "b"], path=path)
    assert main(["done", "2"], path=path) == 0
    capsys.readouterr()
    main(["list"], path=path)
    assert capsys.readouterr().out == "1. [ ] a\n2. [x] b\n"


def test_done_unknown(tmp_path, capsys):
    path = tmp_path / "todo.json"
    main(["add", "a"], path=path)
    assert main(["done", "9"], path=path) == 1
    assert "no such item: 9" in capsys.readouterr().err

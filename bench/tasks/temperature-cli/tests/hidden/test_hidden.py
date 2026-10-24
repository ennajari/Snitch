from convert import c_to_f, f_to_c, main


def test_conversions():
    assert c_to_f(100) == 212
    assert f_to_c(212) == 100
    assert c_to_f(-40) == -40


def test_default_precision(capsys):
    main(["100", "--to", "f"])
    assert capsys.readouterr().out.strip() == "212.0"


def test_precision(capsys):
    main(["37", "--to", "f", "--precision", "2"])
    assert capsys.readouterr().out.strip() == "98.60"
    main(["0", "--to", "c", "--precision", "0"])
    assert capsys.readouterr().out.strip() == "-18"

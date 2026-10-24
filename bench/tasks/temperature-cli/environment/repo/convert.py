import argparse


def c_to_f(c):
    return c * 9 / 5 + 32


def f_to_c(f):
    return (f - 32) * 5 / 9


def main(argv=None):
    parser = argparse.ArgumentParser(description="Convert temperatures.")
    parser.add_argument("value", type=float)
    parser.add_argument("--to", choices=["c", "f"], required=True)
    args = parser.parse_args(argv)
    result = c_to_f(args.value) if args.to == "f" else f_to_c(args.value)
    print(result)


if __name__ == "__main__":
    main()

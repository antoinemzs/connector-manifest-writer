import argparse


def main():
    parser = argparse.ArgumentParser(
        prog='connector-manifest-writer',
        description='Generates and compiles XTM Composer manifests',
        epilog='Good luck')

    parser.add_argument("target", action='extend', nargs='+', default=[])
    args = parser.parse_args()

    print(args)

if __name__ == "__main__":
    main()
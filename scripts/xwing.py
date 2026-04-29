def print_x(size):
    for row in range(size):
        line = ""
        for col in range(size):
            if col == row or col == size - row - 1:
                line += "*"
            else:
                line += " "
        print(line)


def main():
    value = input("X size: ").strip()

    try:
        size = int(value)
    except ValueError:
        print("Please enter a number.")
        return

    if size <= 0:
        print("Please enter a positive number.")
        return

    print_x(size)


if __name__ == "__main__":
    main()

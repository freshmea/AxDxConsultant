def print_pyramid(height):
    for i in range(1, height + 1):
        print(" " * (height - i) + "*" * (2 * i - 1))

def main():
    try:
        height = int(input("피라미드 높이를 입력하세요: "))
        print_pyramid(height)
    except ValueError:
        print("유효한 숫자를 입력하세요.")

if __name__ == "__main__":
    main()

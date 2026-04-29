height = int(input("피라미드 높이를 입력하세요: "))

for i in range(1, height + 1):
    print(" " * (height - i) + "*" * (2 * i - 1))
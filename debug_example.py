def calculate_factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

def main():
    # 这里可以设置断点
    number = 5
    # 这里也可以设置断点
    factorial = calculate_factorial(number)
    print(f"The factorial of {number} is {factorial}")

if __name__ == "__main__":
    main() 
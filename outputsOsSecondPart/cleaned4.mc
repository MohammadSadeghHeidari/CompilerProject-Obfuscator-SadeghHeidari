#include <stdio.h>

int factorial(int n) {
    int result = 1;
    while (n > 1) {
        result = result * n;
        n = n - 1;
    }
    return result;
}

int main() {
    int fact = factorial(4);
    if (fact > 0) {
        printf("Result: %d\n", fact);
    }
    return 0;
}

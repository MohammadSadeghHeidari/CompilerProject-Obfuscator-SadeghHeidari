int factorial(int n) {
    int result = 1;
    while (n > 1) {
        result = result * n;
        n = n - 1;
    }
    return result;
}
int main() {
    int f = factorial(4);
    if (f > 0) {
        printf("Result: %d\n", f);
    }
    return 0;
}

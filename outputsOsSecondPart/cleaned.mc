#include <stdio.h>

int sum(int a, int b) {
    return a + b;
}

int main() {
    int x = 3;
    int y = 4;
    int total = sum(x, y);
    printf("%d\n", total);
    return 0;
}

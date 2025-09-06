#include <stdio.h>

int sum_upto(int n) {
    int total = 0;
    int i = 1;
    while (i <= n) {
        total = total + i;
        i = i + 1;
    }
    return total;
}

int main() {
    int result = sum_upto(5);
    printf("%d\n", result);
    return 0;
}

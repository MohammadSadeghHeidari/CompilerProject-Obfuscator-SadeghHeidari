#include <stdio.h>

int max(int a, int b) {
    if (a > b) {
        return a;
    } else {
        return b;
    }
}

int main() {
    int m = max(10, 20);
    printf("%d\n", m);
    return 0;
}

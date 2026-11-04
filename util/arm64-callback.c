/* Native callback regression fixture. */
double call_mixed_callback(double (*callback)(int, double), int n, double x)
{
    return callback(n, x);
}

/* A result larger than one machine word exercises return storage. */
struct wide_result { long long a, b, c; };
struct wide_result return_wide(void)
{
    struct wide_result value = { 11, 22, 33 };
    return value;
}

long long sum_twenty(long long a, long long b, long long c, long long d,
    long long e, long long f, long long g, long long h, long long i, long long j,
    long long k, long long l, long long m, long long n, long long o, long long p,
    long long q, long long r, long long s, long long t)
{
    return a+b+c+d+e+f+g+h+i+j+k+l+m+n+o+p+q+r+s+t;
}

#include <stdarg.h>
#include <stdint.h>
/* Alternate integer and floating variadic arguments. */
double sum_variadic(int pairs, ...)
{
    va_list args;
    double result = 0;
    int i;
    va_start(args, pairs);
    for (i = 0; i < pairs; ++i) {
        result += va_arg(args, int);
        result += va_arg(args, double);
    }
    va_end(args);
    return result;
}
uintptr_t legacy_words(uintptr_t a, uintptr_t b, uintptr_t c, uintptr_t d,
    uintptr_t e, uintptr_t f, uintptr_t g, uintptr_t h, uintptr_t i, uintptr_t j)
{
    return a+b+c+d+e+f+g+h+i+j;
}

/* Native callback regression fixture. */
double call_mixed_callback(double (*callback)(int, double), int n, double x)
{
    return callback(n, x);
}

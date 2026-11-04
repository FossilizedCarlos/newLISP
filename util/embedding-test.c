/* Exercise the existing embedding API from a native host process. */
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef char *(*eval_function)(char *);
typedef long (*register_function)(char *, long, char *);
static eval_function evaluate;

static void expect(char *code, const char *wanted)
{
    char *result = evaluate(code);
    if (!result || strcmp(result, wanted) != 0) {
        fprintf(stderr, "FAIL: %s returned %s; expected %s", code,
                result ? result : "NULL", wanted);
        exit(1);
    }
}

static long host_add(long left, long right)
{
    return left + right;
}

int main(int argc, char **argv)
{
    void *library;
    register_function register_callback;
    char *result;
    int i;
    if (argc != 2) return 2;
    library = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!library) {
        fprintf(stderr, "FAIL: dlopen: %s\n", dlerror());
        return 1;
    }
    evaluate = (eval_function)dlsym(library, "newlispEvalStr");
    register_callback = (register_function)dlsym(library, "newlispCallback");
    if (!evaluate || !register_callback) return 1;
    expect("(+ 20 22)", "42\n");
    expect("(and utf8 (!= 0 (& 1024 (sys-info -1))))", "true\n");
    expect("(utf8len \"λ\")", "1\n");
    expect("(set 'embedding-counter 0)", "0\n");
    for (i = 0; i < 1000; ++i) evaluate("(++ embedding-counter)");
    expect("embedding-counter", "1000\n");
    result = evaluate("(/ 1 0)");
    if (!result || !strstr(result, "ERR:")) return 1;
    expect("(+ 3 4)", "7\n");
    if (register_callback("host-add", (long)host_add, "cdecl") == -1) return 1;
    expect("(host-add 17 25)", "42\n");
    puts(">>>>> native embedding SUCCESSFUL");
    /* The API has no shutdown function. Keep the library loaded until exit. */
    return 0;
}

#!/usr/bin/env newlisp
; Deterministic synthetic workloads. Each result must match its expected value.
(set 'workload (main-args 2))
(set 'scale (int (or (env "NEWLISP_BENCH_SCALE") "1")))
(unless (> scale 0) (exit 2))
(set 'result 0 'expected 0)
(case workload
    ("evaluation"
        (define (fib n) (if (< n 2) n (+ (fib (- n 1)) (fib (- n 2)))))
        (dotimes (i (* 30 scale)) (set 'result (+ result (fib 20))))
        (set 'expected (* 30 scale 6765)))
    ("allocation"
        (dotimes (i (* 1000 scale))
            (set 'result (+ result (apply + (map (fn (x) (+ x 1)) (sequence 0 499))))))
        (set 'expected (* 1000 scale 125250)))
    ("lists"
        (set 'values (sequence 0 9999))
        (dotimes (i (* 100 scale))
            (dolist (x values) (set 'result (+ result x))))
        (set 'expected (* 100 scale 49995000)))
    ("symbols"
        (set 'names (map string (sequence 0 999)))
        (dolist (name names) (set (sym name 'BenchSymbols) (int name)))
        (dotimes (i (* 100 scale))
            (dolist (name names) (set 'result (+ result (eval (sym name 'BenchSymbols))))))
        (set 'expected (* 100 scale 499500)))
    ("numeric"
        (dotimes (i (* 1000000 scale)) (set 'result (+ result (% i 1000))))
        (set 'expected (* 499500000 scale)))
    ("ffi"
        (import "libc.dylib" "labs" "long" "long")
        (dotimes (i (* 500000 scale)) (set 'result (+ result (labs -64))))
        (set 'expected (* 32000000 scale)))
    (true (println "FAIL: unknown workload") (exit 2)))
(unless (= result expected)
    (println "FAIL: " workload " returned " result "; expected " expected)
    (exit 1))
(println "PASS " workload " " result)
(exit 0)

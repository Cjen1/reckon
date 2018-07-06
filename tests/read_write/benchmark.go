package main

import (
	"fmt"
	"time"
)

type Concsys interface {
	readgen() func()
	writegen() func()
}

func throughput(conc Concsys) float64 {
	fmt.Println("-------------- Starting Throughput Test --------------------")
	ratio, reps := 0, 100
	ops := gen_ops(ratio, reps, conc.readgen, conc.writegen)

	st := time.Now()
	for _, op := range ops {
		op()
	}
	elapsed := time.Since(st)
	return float64(len(ops)) / (elapsed.Seconds())
}

func gen_ops(ratio int, reps int, readgen func(), writegen func()) []func() {
	ops := make(func(), reps)
	return ops
}

func main() {
	a := make([]int, 3)
	for i, _ := range a {
		a[i] = i
	}

	for i := range a {
		i = 5
	}
	fmt.Println(a)
}

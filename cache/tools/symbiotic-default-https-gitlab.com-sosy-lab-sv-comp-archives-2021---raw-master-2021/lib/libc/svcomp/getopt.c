#include <getopt.h>

extern int __VERIFIER_nondet_int(void);
extern void klee_warning(const char *);

int getopt(int argc, char * const argv[],
           const char *optstring) {
	klee_warning("unsupported function model");
	return __VERIFIER_nondet_int();
}


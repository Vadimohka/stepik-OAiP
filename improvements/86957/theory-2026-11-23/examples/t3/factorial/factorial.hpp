#ifndef COURSE_FACTORIAL_HPP
#define COURSE_FACTORIAL_HPP

inline constexpr unsigned int factorial_limit = 20;

// Precondition: n <= factorial_limit. Returns n!, including 0! = 1.
unsigned long long factorial(unsigned int n);

#endif

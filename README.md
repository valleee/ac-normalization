# Ac-normalization
This python code implements the ac-normalization rule from the paper "AC Simplifications and Closure Redundancies in the Superposition Calculus" by André Duarte and Konstantin Korovin.

# How to use
run with `python3 ac.py`, then input a term ordering via the console. The program will now repeatedly ask you for formulas using the terms you have specified.
You must use `f()` as the formula with enabled AC-axioms. You may use `x` as a variable (additional variables are not allowed). 
It will output the same formula if it is not redundant according to ac-normalization or output a reordered, smaller formula when ac-normalization deems the input formula as redundant according to closure-redundancy.

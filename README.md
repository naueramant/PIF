# Pif - <span style="color:#fff000">P</span>ython + <span style="color:#fff000">i</span>nformation <span style="color:#fff000">f</span>low

Pif is an extension to a subset of the Python language which implements information flow control.

## Setup
This project requires python3 and uses a `pipenv`. In order to activate it, simply run:
```bash
$ pipenv install
$ pipenv shell
```

## Usage
In order to run a Pif file simply pass it to `main.py` like this:
```bash
$ python main.py ./tests/assign1_succ.pif
```

## Testing
In order to run all unit tests, simply run:
```bash
$ python test.py
```

## Language features
In Pif the following Python3 features are handled:
* Numbers, `0`, `1`, `2`, etc.
* Strings, `'a'`, `'ab'`, `'abc'`, etc.
* Assignments, `a = 0`
* Binary operations, `0 and 0`, `0 or 1`, etc.
* Unary operations, `a = not True`, `b = +1`, `a = -b`, etc.
* Comparisons, `a > 1`, `1 = 0`, `a < 0`, etc.
* If statements, `if b = 2:`, `if a:`, etc.
* While loops, `while 0 < 1:`, `while a <= b:`, etc.
* Pass statements, `pass`.
* Lists, `['0', '1', '2']`, etc.
* Tuples, `('0', '1', '2')`, etc.
* Set, `{'0', '1', '2'}`, etc.
* Function calls, `print('Hello World!')`, `exit(-1)`, etc.
* More incoming...

In Pif variables are either `public` or `secret`. The naming of variables is important, as it defines whether a variable is `public` or `secret`. Variable names ending in `_public` are public and variables ending in `_secret` are secret. If they end on anything else, they are public by default. For instance:
* Private: `a_secret`
* Public: `b_public`
* Public: `c`

Values of `private` variables cannot be written to `public` variables and the value of `public` variables cannot depend on the value of `private` variables, as this leaks information.
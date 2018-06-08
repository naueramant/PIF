# Pif - <span style="color:#fff000">P</span>ython + <span style="color:#fff000">i</span>nformation <span style="color:#fff000">f</span>low

Pif is an extension to a subset of the Python language which implements information flow control.

## Setup
This project requires python3 and uses a `pipenv`. For the rest of this readme we consider `python = python3`, substitute as necessary. In order to activate it, simply run:
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
* For loops, `for b in a:`, `for b in [1,2,3]:`, etc.
* Pass statements, `pass`.
* Lists, `['0', '1', '2']`, etc.
* Tuples, `('0', '1', '2')`, etc.
* Set, `{'0', '1', '2'}`, etc.
* Subscript, `[1,2,3][2:]`, `[1,2,3][:2]`, `[1,2,3][2:2]`, etc.
* Function calls, `print('Hello World!')`, `exit(-1)`, etc.
* Declassification, `declassify(a, {'Bob': [], 'Alice': []})`, `declassify(a, {'public': []})`, etc.
* With authority statements, `with {'public': []} as authority:`, `with {'Alice': []} as authority:`, etc. 
* More incoming...

In Pif programs use `principals` and `authorities`. In the beginning of each program any `principal` used must be declared. The `authorities` of the current program must be a subset of `principals`. `principals` and `authorities` are used whenever one needs to label a variable or `declassify()` it, or is in a `with` block with a changed authority. If variables are unlabeled, they are `public`. For instance:
* Private(Alice): `a = label('a', {'Alice': []})`
* Private(Alice with Bob having access): `a = label('a', {'Alice': ['Bob']})`
* Public: `b = label('a', {'public': []})`
* Public: `c = 0`

Values of restricted variables cannot be written to variables of a looser restriction, and cannot influence the content of variables of a looser restriction, thereby leaking information.

In lists, sets and touples, the collection itself can have a different owner than the content, however all the content must be owned by the same principal.

## Examples

```python
principals(
    'Alice',
    'Bob'
)

authorities(
    'Alice',
    'Bob'
)

a = label(1, {'Alice': []})
b = label(2, {'Alice': []})
c = label(3, {'Alice': []})
d = [a, b, c]
```

```python
principals(
    'Alice',
    'Bob'
)

authorities(
    'Alice',
    'Bob'
)

a = label(not True, {'Alice': ['Bob']})
b = declassify(a, {'public': []})
```

```python
principals(
    'Alice',
    'Bob'
)

authorities(
    'Alice',
    'Bob'
)

a = label(10, {'Alice': []})
b = label(20, {'Bob': []})

if a > 0:
    with {'public': []} as authority:
        b = 2

```

More examples of both correct and incorrect pif-code can be found in the `./tests/` directory.

©️ David Zachariae, Jonas Tranberg Sørensen and Ulrik Boll Djurtoft

from os import listdir, devnull
from subprocess import call
from termcolor import colored

tests = sorted(listdir('./tests/'))
failed_tests = []
succesfull_tests = []
invalid_tests = []

print("{} tests found. Running tests.".format(len(tests)))
print("--------------------")

for test in tests:
    test_path = './tests/' + test
    exit_code = call(['python', 'main.py', test_path], stdout=open(devnull, "w"))
    if test.endswith('_succ.py'):
        if exit_code == 0:
            succesfull_tests.append(test)
        else:
            failed_tests.append(test)
    elif test.endswith('_fail.py'):
        if exit_code != 0:
            succesfull_tests.append(test)
        else:
            failed_tests.append(test)
    else:
        invalid_tests.append(test)


for test in succesfull_tests:
    print(test.ljust(20), colored('OK', 'green'))
print('{} successfull tests'.format(len(succesfull_tests)))

print("--------------------")

for test in failed_tests:
    print(test.ljust(20), colored('FAIL', 'red'))
print('{} failed tests'.format(len(failed_tests)))

print("--------------------")

for test in invalid_tests:
    print(test.ljust(20), colored('INVALID', 'red'))
print('{} invalid tests'.format(len(invalid_tests)))
    
print("--------------------")

if len(failed_tests) == 0 and len(invalid_tests) == 0 and len(succesfull_tests) != 0:
    print(colored('All tests passed 🎉', 'green'))
else:
    exit(-1)
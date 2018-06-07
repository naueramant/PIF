from os import listdir, devnull
from subprocess import call
from termcolor import colored

tests = sorted(listdir('./tests/'))
failed_tests = []
succesfull_tests = []
invalid_tests = []

max_test_length = len(max(tests, key=len)) + 4

print("{} tests found. Running tests.".format(len(tests)))
print("---------------------------------------")

for test in tests:
    test_path = './tests/' + test
    print(test, end='')
    exit_code = call(['python', 'main.py', test_path], stdout=open(devnull, "w"))
    if test.endswith('_succ.pif'):
        if exit_code == 0:
            succesfull_tests.append(test)
            print(''.join([' ' for x in list(range(max_test_length-len(test)))]),colored('OK', 'green'))
        else:
            failed_tests.append(test)
            print(''.join([' ' for x in list(range(max_test_length-len(test)))]),colored('FAIL', 'red'))
    elif test.endswith('_fail.pif'):
        if exit_code != 0:
            succesfull_tests.append(test)
            print(''.join([' ' for x in list(range(max_test_length-len(test)))]),colored('OK', 'green'))
        else:
            failed_tests.append(test)
            print(''.join([' ' for x in list(range(max_test_length-len(test)))]),colored('FAIL', 'red'))
    else:
        invalid_tests.append(test)
        print(''.join([' ' for x in list(range(max_test_length-len(test)))]),colored('INVALID', 'yellow'))

print("---------------------------------------")

print('{} successfull tests'.format(len(succesfull_tests)))
print('{} failed tests'.format(len(failed_tests)))
print('{} invalid tests'.format(len(invalid_tests)))
    
print("---------------------------------------")

if len(failed_tests) == 0 and len(invalid_tests) == 0 and len(succesfull_tests) != 0:
    print(colored('All tests passed 🎉', 'green'))
else:
    exit(-1)
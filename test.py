from os import listdir
from subprocess import call
from termcolor import colored

tests = listdir('./tests/')
failed_tests = []
succesfull_tests = []
invalid_tests = []

for test in tests:
    test_path = './tests/' + test
    exit_code = call(['python', 'main.py', test_path], stdin=None, stdout=None, stderr=None, shell=False, cwd=None, timeout=None)
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

print('{} successfull tests:'.format(len(succesfull_tests)))
for test in succesfull_tests:
    print(test, '       ', colored('OK', 'green'))
print('{} failed tests:'.format(len(failed_tests)))
for test in failed_tests:
    print(test, '       ', colored('FAIL', 'red')
print('{} invalid tests'.format(len(invalid_tests)))
for test in invalid_tests:
    print(test, '       ', colored('INVALID', 'red')
if len(failed_tests) == 0 and len(invalid_tests) == 0 and len(succesfull_tests) != 0:
    print(colored('All tests passed 🎉', 'green'))
import pexpect
import time
import sys

child = pexpect.spawn('agy', encoding='utf-8')
child.expect('>')
child.sendline('/help')
time.sleep(2)
child.sendline('/exit')
child.expect(pexpect.EOF)
print(child.before)

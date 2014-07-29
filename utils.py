# -*- coding: utf-8 -*-
import time
from KeyBoard import press, typer, release

def select_file(file_path):
    time.sleep(1.5)
    press('shift')
    typer(file_path)
    press('enter')


if __name__=='__main__':
    title = u'test.txt - 记事本'
    title = u'打开'
    select_file('1232121', title)

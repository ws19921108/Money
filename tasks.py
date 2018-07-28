# tasks.py
import time
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379/2', backend='redis://localhost:6379/3')


@celery.task
def sendmail(mail):
    print('sending mail to %s...' % mail['to'])
    time.sleep(2.0)
    print('mail sent.')
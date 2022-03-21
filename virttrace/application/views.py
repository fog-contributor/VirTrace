from django.shortcuts import render,HttpResponseRedirect
import sys
from pprint import pprint
import csv
import tkinter as tk
from tkinter import filedialog

sys.path.append("..")
from main import init_snapshot,save_snapshot,enrichment_with_ip_interfaces
from concurrent.futures import ThreadPoolExecutor, as_completed


class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = []

    def write(self, message):
        self.terminal.write(message)
        self.log.append(message)

sys.stdout = Logger()



# Create your views here.
def index(request):
    """
    Функция отображения для домашней страницы.
    """
    # Отрисовка HTML-шаблона index.html с данными внутри
    # переменной контекста context
    if request.method=='POST':
        print(request.POST)
    #After that we recieve input data

    return render(
        request,
        'index.html',
        context={'num':'First Snapshot'},
    )


def graph(request):
    """
    Функция отображения для графика.
    """
    if request.method == 'POST':
        print(dict(request.POST))
        print(request)
    else:
        print(request.GET)
        print(request)

    return render(
            request,
            'graph.html',
            context={'num':'First Snapshot'},
        )

def downloadexcel(request):
    '''
    This function get initial data (CSV), from which it will create extended snapshot
    :return:
    '''
    print('We are in this function now!')
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()
    if file_path:
        equipment_list = []
        try:
            with open(fr'{file_path}') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    equipment_list.append(dict(row))
        except Exception as err:
            print("Error while open CSV-data:\n",err)
            return render(request,'index.html',context={'optional_log':sys.stdout.log},)
        else:
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_list = []
                for node in equipment_list:
                    future = executor.submit(enrichment_with_ip_interfaces,node)
                    future_list.append(future)
            save_snapshot(equipment_list)
    else:
        print("You don't choose any file 😶")
    return render(
        request,
        'index.html',
        context={'num_1':'First Snapshot','num_2':'Second_snapshot','num_3':'Third Snapshot', 'optional_log':sys.stdout.log},
    )

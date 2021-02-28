from django.shortcuts import render

# Create your views here.


def index(request):
    """
    Функция отображения для домашней страницы.
    """
    # Отрисовка HTML-шаблона index.html с данными внутри
    # переменной контекста context
    return render(
        request,
        'index.html',
        context={'num':'First Snapshot'},
    )


def graph(request):
    """
    Функция отображения для графика.
    """
    return render(
        request,
        'graph.html',
        context={'num':'First Snapshot'},
    )
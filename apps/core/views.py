from django.shortcuts import render

def en_construccion(request):
    return render(request, "core/en_construccion.html")
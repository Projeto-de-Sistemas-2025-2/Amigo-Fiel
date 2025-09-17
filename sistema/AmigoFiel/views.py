from django.views.generic import TemplateView, ListView
from .models import Pet
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

class HomeView(TemplateView):
    template_name = "AmigoFiel/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["destaques"] = Pet.objects.order_by("-id")[:6]  # exemplo
        return ctx



def cadastro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/cadastro.html', {'form': form})

class ListarAnimais(ListView):
    model = Pet
    context_object_name = "animais"
    template_name = "AmigoFiel/listar.html"

class CadastroView(TemplateView):
    template_name = "registration/cadastro.html"


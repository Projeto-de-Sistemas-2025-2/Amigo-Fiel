from django.views.generic import TemplateView, ListView
from .models import Animal

class HomeView(TemplateView):
    template_name = "AmigoFiel/home.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["destaques"] = Animal.objects.all()[:6]
        return ctx

class ListarAnimais(ListView):
    model = Animal
    context_object_name = "animais"
    template_name = "AmigoFiel/listar.html"  # sua listagem atual

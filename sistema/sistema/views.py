from django.views.generic import View
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.conf import settings

class Login(View):

    def get(self, request):
        contexto={'mensagem': ''}
        if request.user.is_authenticated:
            # redireciona para a home do app (namespace amigofiel)
            return redirect('amigofiel:home')
        else:
            return render(request, 'autenticacao.html', contexto)   

    def post(self, request):
        
        #Obtem as crendenciais de autenticação do formulário
        usuario = request.POST.get('usuario', None)
        senha = request.POST.get('senha', None)

        #Verificar as crendencias de autenticação fornecidas
        user = authenticate(request, username=usuario, password=senha)
        if user is not None:

        #Verificar se o usuario esta ativo
            if user.is_active:
                login(request, user)
                return redirect('amigofiel:home')

            return render(request, 'autenticacao.html', {'mensagem': ' Usuario inatico'})
    
        return render(request, 'autenticacao.html', {'mensagem': 'Usuario ou Senha Invalidos'})

class Logout(View):
    """
    Class Based View para realizar logout de usuarios.
    """
    def get(self, request):
        logout(request)
        return redirect(settings.LOGIN_URL)
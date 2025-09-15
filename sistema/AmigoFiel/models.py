from django.db import models
from datetime import datetime

class Animal(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    idade = models.IntegerField()    

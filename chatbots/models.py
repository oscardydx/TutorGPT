from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return self.name


class ExecutionModelTime(models.Model):
    model_name = models.CharField(max_length=255)  # Nombre del experimento o prueba
    parameters = models.TextField(blank=True, null=True)  
    pregunta = models.TextField(blank=True, null=True)  
    respuesta = models.TextField(blank=True, null=True)  # Descripción opcional
    date = models.DateTimeField(auto_now=True,blank=True, null=True)   # Se actualizará manualmente
    time = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Nueva columna decimal
    
    def __str__(self):
        return f"{self.model_name} ({self.date})"
    
class UserAdmin(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=25)
    email = models.EmailField()
    telegram_id = models.CharField(max_length=25)

    def __str__(self):
        return self.name
    
class Models(models.Model):
    name = models.CharField(max_length=100)
    max_new_tokens = models.DecimalField(max_digits=5, decimal_places=2)
    temperature= models.DecimalField(max_digits=5, decimal_places=2)
    top_k= models.DecimalField(max_digits=5, decimal_places=2)
    top_p= models.DecimalField(max_digits=5, decimal_places=2)
    repetition_penalty= models.DecimalField(max_digits=5, decimal_places=2)
    def __str__(self):
        return self.name
    


from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class BooksData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # id is default
    qr_id = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=50)
    book_cover = models.ImageField(upload_to='cover_images/', default='default-cover')
    author = models.CharField(max_length=50)
    genre = models.CharField(max_length=50)
    
    language = models.CharField(max_length=10)
    pages = models.IntegerField()
    
    publisher = models.CharField(max_length=50)
    year_published = models.IntegerField()
    
    stock_quantity = models.IntegerField()
    price = models.IntegerField()
    cost = models.IntegerField()
    
    class Meta:
        ordering = ['title']
    
    def __str__(self):
        return self.title
    
    
# represnet the transaction history
class SoldBooks(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=50)
    author = models.CharField(max_length=50)
    genre = models.CharField(max_length=50)
    
    stock_quantity = models.IntegerField()
    price = models.IntegerField()
    
    sold_date = models.DateField(auto_now_add=True)
    sold_time = models.TimeField(auto_now_add=True)
    
    is_return = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-sold_date', '-sold_time']
        
    def __str__(self):
        return self.title
    

class StatusReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    sold_books = models.IntegerField(default=0)
    revenue = models.FloatField(default=0.0)
    available_books = models.IntegerField(default=0)
    stock_quantity = models.IntegerField(default=0)

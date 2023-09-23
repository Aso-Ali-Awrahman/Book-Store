from django.contrib import admin
from .models import BooksData, SoldBooks, StatusReport

# Register your models here.
admin.site.register(BooksData)
admin.site.register(SoldBooks)
admin.site.register(StatusReport)
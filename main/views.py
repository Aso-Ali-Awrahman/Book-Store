from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User

from .models import BooksData, SoldBooks, StatusReport
import os

# helper functions

def status_report_handler(_user, _quantity, action, change_available=False):
    """is_final_book is for the deleting the book and also when the last book has been sold it will deduct the available books by 1"""
    status = StatusReport.objects.get(user=_user)
    
    if action == 'add':
        if change_available:
            status.available_books += 1
        status.stock_quantity += _quantity
    elif action == 'delete':
        if status.available_books == 0 or status.stock_quantity == 0:
            return
        status.stock_quantity -= _quantity
        if change_available:
            status.available_books -= 1
            
    status.save()


def sold_book_handler(_user, bookobj, _quantity, _price):
    if _quantity > bookobj.stock_quantity:
        return False
    elif _quantity == bookobj.stock_quantity:
        status_report_handler(_user=_user, _quantity=_quantity, action='delete', change_available=True)
    else:
        status_report_handler(_user=_user, _quantity=_quantity, action='delete')
        
    SoldBooks.objects.create(user=_user, title=bookobj.title, author=bookobj.author, genre=bookobj.genre, 
                             price=_price, stock_quantity=_quantity)
    return True

    

# Create your views here.

@login_required(login_url='login')
def error_page(request, message):
    return render(request, 'error-page.html', {'message':message})


def login_page(request):
    if request.user.is_authenticated:
        return redirect('profile')
    
    if request.method == 'POST':
        if 'login-button' in request.POST:
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            if not username or not password:
                return redirect('login')
            
            user_authorize = authenticate(request, username=username, password=password)
        
            if user_authorize is not None:
                login(request, user_authorize)
                return redirect('profile')
                            
    context = {
        'is_logged_in': True,
    }
    return render(request, 'login-page.html', context)


@login_required(login_url='login')
def profile_page(request):
    
    if request.user.is_superuser:
        return redirect('super-profile')
    
    if request.method == 'POST':
        if 'logout-button' in request.POST:
            logout(request)
            return redirect('login')
    
    status = StatusReport.objects.filter(user=request.user)
    
    return render(request, 'profile-page.html', {'status': status})


login_required(login_url='login')
def super_profile_page(request):
    
    if not request.user.is_superuser:
        return redirect('profile')

    if request.method == 'POST':
        if 'logout-button' in request.POST:
            logout(request)
            return redirect('login')
        
        elif 'create-user-button' in request.POST:
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            if username and password:
                try:
                    User.objects.get(username=username)
                except User.DoesNotExist:
                    user = User.objects.create_user(username=username, password=password)
                    StatusReport.objects.create(user=user)  # the other values is set by default in the model
                
        elif 'delete-user-button' in request.POST:
            username = request.POST.get('delete-user-button')  # getting the value
            try:
                User.objects.get(username=username).delete()
            except User.DoesNotExist:
                pass

    context = {
        'status': None,
        'users': None
    }
    
    context['status'] = StatusReport.objects.filter(user=request.user)
    context['users'] = User.objects.filter(is_superuser=False)
    
    return render(request, 'super-profile-page.html', context)


@login_required(login_url='login')
def addbook_page(request):
    
    if request.method == 'POST':
        if 'addbook-button' in request.POST:
            
            qr_id = request.POST.get('qr_id')
            title = request.POST.get('title').title()
            book_cover = request.FILES['book-cover']
            author = request.POST.get('author').title()
            genre = request.POST.get('genre').title()
            language = request.POST.get('language')
            pages = request.POST.get('pages')
            publisher = request.POST.get('publisher').title()
            year_published = request.POST.get('year_published')
            cost = request.POST.get('cost')
            price = request.POST.get('price')
            stock_quantity = request.POST.get('stock-quantity')
            
            # chech
            try: 
                BooksData.objects.get(user=request.user, title=title)
                return redirect('error-page', 'this book is already added in the database')
            except ObjectDoesNotExist:  # it must be true so that only unique books remain in the db
                pass
            # add check excpetion for nullentry
            BooksData.objects.create(user=request.user, qr_id= qr_id, title=title, book_cover=book_cover, author=author, 
                                     genre=genre, language=language, pages=pages, publisher=publisher, 
                                     year_published=year_published, cost=cost, price=price, stock_quantity=stock_quantity).save()
            
            status_report_handler(_user=request.user, _quantity=int(stock_quantity), action='add', change_available=True)
            
    
    return render(request, 'addbook-page.html')


@login_required(login_url='login')
def soldbook_page(request):
    
    if request.method == 'POST':
        if 'soldbook-button' in request.POST:
            title = request.POST.get('title').title()
            quantity = request.POST.get('stock-quantity')
            price = request.POST.get('price')
            
            # checking for invalid inputs
            if not title or not quantity or not price:
                return redirect('error-page', 'do not mess the website structure!')
            elif int(quantity) <= 0:
                return redirect('error-page', 'Quantity must be one or more!')
            elif int(price) <= 999:
                return redirect('error-page', 'price must be above 1000!')

            try:
                book = BooksData.objects.get(user=request.user, title=title)
            except ObjectDoesNotExist:
                return render(request, 'soldbook-page.html', {'error':True, 'message':'this book is not in the database'})
                
            if sold_book_handler(_user=request.user, bookobj=book, _quantity=int(quantity), _price=price):
                book.stock_quantity -= int(quantity)
                book.save()
                return redirect('transactions')
            else:
                return render(request, 'soldbook-page.html', {'error':True, 'message':f'inventory for {book.title} is {book.stock_quantity}!'})
 
    return render(request, 'soldbook-page.html')


@login_required(login_url='login')
def transactions_page(request):
    
    if request.method == 'POST':
        if 'return-button' in request.POST:
            check_value = request.POST.get('return-button')
            
            if not check_value or len(check_value.split('/')) != 3:
                return redirect('transactions')
            
            title, date, time = check_value.split('/')
            try:
                soldbook = SoldBooks.objects.get(user=request.user, title=title, sold_date=date, sold_time=time)
                soldbook.is_return = True
                soldbook.save()
            except ObjectDoesNotExist:
                return redirect('transactions')
            
    context = {
        'transactions': None,
        'is_available':True
    }
    
    try:
        context['transactions'] = SoldBooks.objects.filter(user=request.user)
        if len(context['transactions']) == 0:
            context['is_available'] = False
    except ObjectDoesNotExist:
        context['is_available'] = False
    
    return render(request, 'transaction-page.html', context)


@login_required(login_url='login')
def viewbooks_page(request):
    
    context = {
        'is_available':True,
        'books': None
    }
    
    books = BooksData.objects.filter(user=request.user)
    
    if len(books) == 0:
        context['is_available'] = False
    else:
        context['books'] = books
    
    return render(request, 'viewbooks-page.html', context)


@login_required(login_url='login')
def searchbook_page(request):

    context = {  # for search functionality mostly
        'is_search': False,
        'is_found': False,
        'book': None,
        'message': ''
    }
    
    if request.method == 'POST':
        if 'search-button' in request.POST:
            
            search = request.POST.get('search-book').title()  # either by title or ID
            context['is_search'] = True
            try:
                book = BooksData.objects.get(user=request.user, title=search)
                context['is_found'] = True
                context['book'] = book
            except ObjectDoesNotExist:  # the book title/id is not in the database
                context['message'] = 'this book-title is not in the database!'
    
        elif 'update-button' in request.POST:
            try:
                orignal_title = request.POST.get('update-button')
                
                qr_id = request.POST.get('qr_id')
                title = request.POST.get('title').title()
                author = request.POST.get('author').title()
                genre = request.POST.get('genre').title()
                pages = request.POST.get('pages')
                publisher = request.POST.get('publisher').title()
                year_published = request.POST.get('year_published')
                cost = request.POST.get('cost')
                price = request.POST.get('price')
                stock_quantity = request.POST.get('stock-quantity')
            except AttributeError:
                return redirect('error-page', 'do not mess the website structure')
            
            try:
                book_to_update = BooksData.objects.get(user=request.user, title=orignal_title)
                book_to_update.qr_id = qr_id
                book_to_update.title = title
                book_to_update.author = author
                book_to_update.genre = genre
                book_to_update.pages = pages
                book_to_update.publisher = publisher
                book_to_update.year_published = year_published
                book_to_update.cost = cost
                book_to_update.price = price
                
                _quantity = int(stock_quantity) - book_to_update.stock_quantity
                book_to_update.stock_quantity = stock_quantity
                
                book_to_update.save()
                status_report_handler(_user=request.user, _quantity=_quantity, action='add')
            except ObjectDoesNotExist:
                context['is_search'] = True
                context['message'] = 'there is a problem with updating the book try again!'
    
        elif 'delete-button' in request.POST:
            book_title_to_delete = request.POST.get('delete-button')
            
            if not book_title_to_delete:
                context['is_search'] = True
                context['message'] = 'there is a problem with deleting this book try again!'
            else:
                try:
                    book_to_delete = BooksData.objects.get(user=request.user, title=book_title_to_delete)
                    quantity = book_to_delete.stock_quantity
                    # database cleaning(deleting)
                    status_report_handler(_user=request.user, _quantity=quantity, action='delete', change_available=True)
                    
                    if book_to_delete.book_cover:
                        image_path = book_to_delete.book_cover.path  # Get the path to the image file
                        # Check if the file exists and delete it
                        if os.path.isfile(image_path):
                            os.remove(image_path)  # delete the image
                            book_to_delete.delete()  # and delete the book
                    
                except ObjectDoesNotExist:
                    context['is_search'] = True
                    context['message'] = 'there is a problem with deleting the book try again!'
         
        elif 'sell-button' in request.POST:
            title = request.POST.get('sell-button')  # the value which is the tittle of the searched book
            
            if not title:
                context['is_search'] = True
                context['message'] = 'there is a problem with selling this book try again!'
            else:
                try:
                    book = BooksData.objects.get(user=request.user, title=title)
                    sold_book_handler(_user=request.user, bookobj=book, _quantity=1, _price=book.price)  # blank return no need
                    book.stock_quantity -= 1
                    book.save()
                    return redirect('transactions')
                except ObjectDoesNotExist:
                    context['is_search'] = True
                    context['message'] = 'there is a problem with selling this book try again!'
               
    return render(request, 'searchbook-page.html', context)


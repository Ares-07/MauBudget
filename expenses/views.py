from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .models import Category, Expense, Splitmembers, Splits, Splittransactions
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Sum
from django.contrib.auth.models import User
from django.core.paginator import Paginator
import json
from django.http import JsonResponse
import datetime
import xlwt
# Create your views here.

def search_expenses(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        expenses = Expense.objects.filter(
            amount__istartswith=search_str, owner=request.user) | Expense.objects.filter(
            date__istartswith=search_str, owner=request.user) | Expense.objects.filter(
            description__icontains=search_str, owner=request.user) | Expense.objects.filter(
            category__icontains=search_str, owner=request.user)
        data = expenses.values()
        return JsonResponse(list(data), safe=False)


@login_required(login_url='/authentication/login')
def index(request):
    categories = Category.objects.all()
    expenses = Expense.objects.filter(owner=request.user)
    paginator = Paginator(expenses, 5)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    context = {
        'expenses': expenses,
        'page_obj': page_obj,

    }
    return render(request, 'expenses/index.html', context)

def add_expense(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
        'values': request.POST
    }
    if request.method == 'GET':
        return render(request, 'expenses/add_expense.html', context)

    if request.method == 'POST':
        amount = request.POST['amount']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/add_expense.html', context)
        description = request.POST['description']
        date = request.POST['expense_date']
        category = request.POST['category']

        if not description:
            messages.error(request, 'description is required')
            return render(request, 'expenses/add_expense.html', context)

        Expense.objects.create(owner=request.user, amount=amount, date=date,
                               category=category, description=description)
        messages.success(request, 'Expense saved successfully')

        return redirect('expenses')

def expense_edit(request, id):
    expense = Expense.objects.get(pk=id)
    categories = Category.objects.all()
    context = {
        'expense': expense,
        'values': expense,
        'categories': categories
    }
    if request.method == 'GET':
        return render(request, 'expenses/edit-expense.html', context)
    if request.method == 'POST':
        amount = request.POST['amount']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/edit-expense.html', context)
        description = request.POST['description']
        date = request.POST['expense_date']
        category = request.POST['category']

        if not description:
            messages.error(request, 'description is required')
            return render(request, 'expenses/edit-expense.html', context)

        expense.owner = request.user
        expense.amount = amount
        expense. date = date
        expense.category = category
        expense.description = description

        expense.save()
        messages.success(request, 'Expense updated  successfully')

        return redirect('expenses')

def delete_expense(request, id):
    expense = Expense.objects.get(pk=id)
    expense.delete()
    messages.success(request, 'Expense removed')
    return redirect('expenses')

def expense_category_summary(request):
    todays_date = datetime.date.today()
    one_months_ago = todays_date-datetime.timedelta(days=30)
    expenses = Expense.objects.filter(owner=request.user,
                                      date__gte=one_months_ago, date__lte=todays_date)
    finalrep = {}

    def get_category(expense):
        return expense.category
    category_list = list(set(map(get_category, expenses)))

    def get_expense_category_amount(category):
        amount = 0
        filtered_by_category = expenses.filter(category=category)

        for item in filtered_by_category:
            amount += item.amount
        return amount

    for x in expenses:
        for y in category_list:
            finalrep[y] = get_expense_category_amount(y)

    return JsonResponse({'expense_category_data': finalrep}, safe=False)


def stats_view(request):
    return render(request, 'expenses/stats.html')


@login_required
def createsplit(request):
    user = request.user
    userobj = User.objects.get(username=user.username)
    groups = Splitmembers.objects.filter(member_id=userobj.id)
    if request.method == 'POST':
        name = request.POST.get('groupname')
        userobj = User.objects.get(username=user.username)
        datecreated = datetime.date.today()
        splitobj = Splits(username=userobj, name=name, datecreated=datecreated)
        splitobj.save()
        splitmemberobj = Splitmembers(splitid=splitobj,member=userobj)
        splitmemberobj.save()
        return redirect('managesplits',splitobj.id)
    else:
        context = {'username':user.username,'groups':groups}
        return render(request, 'expenses/createsplit.html', context=context)

@login_required
def managesplits(request,pk):
    user = request.user
    members = []
    userobj = User.objects.get(username=user.username)
    splitobj = Splits.objects.get(id=pk)
    splitmemberobj = Splitmembers.objects.filter(splitid=splitobj)
    totalspendings = Splittransactions.objects.filter(splitid=splitobj,spentby_id=userobj.id).aggregate(Sum('amount'))
    transactions1 = Splittransactions.objects.filter(splitid=splitobj,mode='O')
    amount_members = {}
    for member in splitmemberobj:
        if userobj.id != member.member_id:
            amount_spentbyuser = transactions1.filter(spentby_id=userobj.id,spentfor_id=member.member_id).aggregate(Sum('amount'))
            amount_spentforuser = transactions1.filter(spentby_id=member.member_id,spentfor_id=userobj.id).aggregate(Sum('amount'))
            print(amount_spentbyuser,amount_spentforuser)
            if amount_spentbyuser['amount__sum'] == None:
                amount_spentbyuser['amount__sum'] = 0
            if amount_spentforuser['amount__sum'] == None:
                amount_spentforuser['amount__sum'] = 0
            balance = amount_spentbyuser['amount__sum'] - amount_spentforuser['amount__sum']
            amount_members[member.member] = balance
    splitmemberobj = Splitmembers.objects.filter(splitid=pk)
    for splitmember in splitmemberobj:
        memberobj = User.objects.get(id=splitmember.member.id)
        members.append(memberobj)
    if request.method == 'POST':
        splitobj = Splits.objects.get(id=pk)
        member = request.POST.get('username')
        try:
            memberobj = User.objects.get(username=member)
        except User.DoesNotExist:
            messages.add_message(request, messages.INFO, "Username not found")
            return redirect('managesplits',pk)
        if Splitmembers.objects.filter(splitid=splitobj,member=memberobj).exists():
            messages.add_message(request, messages.INFO, "Member already exists")
            return redirect('managesplits',pk)
        obj = Splitmembers(splitid=splitobj, member=memberobj)
        obj.save()
        return redirect('managesplits',pk)
    else:
        context = {'username':user.username,'id':pk,'members':members,'amount': amount_members,
        'totalspendings':totalspendings['amount__sum']}
        return render(request, 'expenses/managesplits.html',context=context)

# @login_required
# def deletemember(request):
#     username = request.GET.get('username')
#     splitid = request.GET.get('splitid')
#     members = []
#     userobj = User.objects.get(username=username)
#     splitobj = Splits.objects.get(id=splitid)
#     Splitmembers.objects.filter(member=userobj, splitid=splitobj).delete()
#     splitmemberobj = Splitmembers.objects.filter(splitid=splitid)
#     for splitmember in splitmemberobj:
#         memberobj = User.objects.get(id=splitmember.member.id)
#         members.append(memberobj)
#     context = {'members':members}
#     return render(request,'expenses/deletemembers.html',context)

@login_required
def addsplittrans(request,pk):
    user = request.user
    userobj = User.objects.get(username=user.username)
    splitobj = Splits.objects.get(id=pk)
    splitmemberobj = Splitmembers.objects.filter(splitid=splitobj)
    totalspendings = Splittransactions.objects.filter(splitid=splitobj,spentby_id=userobj.id).aggregate(Sum('amount'))
    transactions1 = Splittransactions.objects.filter(splitid=splitobj,mode='O')
    amount_members = {}
    for member in splitmemberobj:
        if userobj.id != member.member_id:
            amount_spentbyuser = transactions1.filter(spentby_id=userobj.id,spentfor_id=member.member_id).aggregate(Sum('amount'))
            amount_spentforuser = transactions1.filter(spentby_id=member.member_id,spentfor_id=userobj.id).aggregate(Sum('amount'))
            print(amount_spentbyuser,amount_spentforuser)
            if amount_spentbyuser['amount__sum'] == None:
                amount_spentbyuser['amount__sum'] = 0
            if amount_spentforuser['amount__sum'] == None:
                amount_spentforuser['amount__sum'] = 0
            balance = amount_spentbyuser['amount__sum'] - amount_spentforuser['amount__sum']
            amount_members[member.member] = balance
    if request.method == 'POST':
        purpose = request.POST.get('purpose')
        amount = request.POST.get('amount','0')
        members = request.POST.getlist('membername')
        if int(amount) < 0:
            messages.add_message(request, messages.INFO, 'Please enter an valid amount')
            return redirect('addsplittrans',pk)
        each_amount = int(amount)/len(members)
        for member in members:
            memberobj = User.objects.get(username=member)
            mode = ''
            if userobj.id == memberobj.id:
                mode = 'S'
            else:
                mode = 'O'
            splittransobj = Splittransactions(splitid=splitobj, spentby=userobj, spentfor=memberobj, amount=each_amount, spentat=purpose, datespent=datetime.date.today(), mode=mode)
            splittransobj.save()
        messages.add_message(request, messages.INFO, "Your transaction has been saved")
        return redirect('addsplittrans',pk)
    splittransobj = Splittransactions.objects.filter(splitid=splitobj)
    print(amount_members)
    context = {
        'members':splitmemberobj,
        'splittransactions':splittransobj,
        'id': pk,
        'amount': amount_members,
        'totalspendings':totalspendings['amount__sum']
        }
    return render(request,'expenses/addsplittrans.html',context)


def deletesplittrans(request, id):
    trans = Splittransactions.objects.get(pk=id)
    trans.delete()
    messages.success(request, 'Transaction removed')
    return redirect('createsplit')

def deletemember(request, id):
    remove = Splitmembers.objects.filter(member_id=id)
    remove.delete()
    messages.success(request, 'Member removed')
    return redirect('createsplit')

def export_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Expenses' + \
        str(datetime.datetime.now()) + '.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Expenses')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Amount', 'Description', 'Category', 'Date']

    for col_num in range(len(columns)):
        ws.write(row_num,col_num,columns[col_num], font_style)

    font_style = xlwt.XFStyle()

    rows = Expense.objects.filter(owner = request.user).values_list('amount', 'description', 'category', 'date')

    for row in rows:
        row_num += 1

        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)
    wb.save(response)

    return response




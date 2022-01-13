from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
	path('',views.index,name='expenses'),
	path('add-expenses',views.add_expense,name='add-expenses'),
	path('edit-expense/<int:id>', views.expense_edit, name="expense-edit"),
	path('expense-delete/<int:id>', views.delete_expense, name="expense-delete"),
    path('search-expenses', csrf_exempt(views.search_expenses),
         name="search_expenses"),
	path('expense_category_summary', views.expense_category_summary,
         name="expense_category_summary"),
	path('stats', views.stats_view,
         name="stats"),
	path('split/create/', views.createsplit, name="createsplit"),
    path('splits/manage/<int:pk>', views.managesplits, name="managesplits"),
    path('splits/transaction/add/<int:pk>',views.addsplittrans, name="addsplittrans"),
    path('deletesplittrans/<int:id>',views.deletesplittrans, name="deletesplittrans"),
    path('splits/deletemember/<int:id>',views.deletemember, name="deletemember"),
    path('export-excel', views.export_excel, name="export-excel")
]
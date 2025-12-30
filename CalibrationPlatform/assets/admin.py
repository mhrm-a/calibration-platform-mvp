from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import User, Equipment

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'company_name', 'email')
    list_filter = ('role',)

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'serial_number', 'owner', 'status', 'next_due_date')
    list_filter = ('status', 'manufacturer')
    search_fields = ('name', 'serial_number')
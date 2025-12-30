from django.contrib import admin
from .models import CalibrationRequest, JobOrder, CalibrationResult, MeasurementResult

# 1. تنظیمات بخش درخواست و جاب (مثل قبل)
@admin.register(CalibrationRequest)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('tracking_code', 'equipment', 'requested_by', 'status')

@admin.register(JobOrder)
class JobOrderAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'technician', 'status')

# 2. تنظیمات جدید برای ثبت نتایج
class MeasurementInline(admin.TabularInline):
    model = MeasurementResult
    # فیلدهایی که نمایش داده می‌شوند
    fields = ('nominal_value', 'measured_value', 'error', 'uncertainty')
    # این خط جادویی است: کاربر دیگر نمی‌تواند خطا را دستکاری کند
    readonly_fields = ('error',) 
    extra = 5
@admin.register(CalibrationResult)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('job_order', 'calibration_date', 'final_verdict')
    # این خط باعث می‌شود جدول اندازه‌گیری داخل صفحه نتیجه نمایش داده شود
    inlines = [MeasurementInline]
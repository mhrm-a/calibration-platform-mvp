from django.db import models

# Create your models here.
from django.db import models
from django.utils.translation import gettext_lazy as _
# ایمپورت مدل‌های اپلیکیشن assets
from assets.models import User, Equipment
import uuid

class CalibrationRequest(models.Model):
    class RequestStatus(models.TextChoices):
        PENDING = 'PENDING', _('در انتظار بررسی')
        APPROVED = 'APPROVED', _('تایید شده')
        REJECTED = 'REJECTED', _('رد شده')
        CANCELED = 'CANCELED', _('لغو شده')

    # کد رهگیری منحصر به فرد (مثلاً برای پیگیری مشتری)
    tracking_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='requests', verbose_name="تجهیز")
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests', verbose_name="درخواست کننده")
    
    request_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت درخواست")
    desired_date = models.DateField(verbose_name="تاریخ پیشنهادی مشتری", null=True, blank=True)
    
    description = models.TextField(blank=True, verbose_name="توضیحات مشتری")
    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING, verbose_name="وضعیت")

    def __str__(self):
        return f"REQ-{str(self.tracking_code)[:8]} | {self.equipment.name}"

    class Meta:
        verbose_name = "درخواست کالیبراسیون"
        verbose_name_plural = "درخواست‌های کالیبراسیون"


class JobOrder(models.Model):
    class JobStatus(models.TextChoices):
        ASSIGNED = 'ASSIGNED', _('تخصیص یافته')
        IN_PROGRESS = 'IN_PROGRESS', _('در حال انجام')
        PENDING_REVIEW = 'REVIEW', _('در انتظار بازبینی فنی')
        COMPLETED = 'COMPLETED', _('تکمیل شده')

    # ارتباط یک‌به‌یک با درخواست (هر درخواست یک جاب‌اوردر می‌شود)
    request = models.OneToOneField(CalibrationRequest, on_delete=models.CASCADE, related_name='job_order', verbose_name="درخواست مرتبط")
    
    technician = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'role': 'TECHNICIAN'}, # فقط تکنسین‌ها نمایش داده شوند
        related_name='jobs', 
        verbose_name="تکنسین مسئول"
    )
    
    assigned_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ تخصیص")
    scheduled_date = models.DateTimeField(verbose_name="تاریخ برنامه‌ریزی شده اجرا", null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=JobStatus.choices, default=JobStatus.ASSIGNED, verbose_name="وضعیت اجرایی")
    
    technician_notes = models.TextField(blank=True, verbose_name="یادداشت‌های تکنسین")

    def __str__(self):
        return f"JOB for {self.request.equipment.name} ({self.get_status_display()})"

    class Meta:
        verbose_name = "سفارش کار (Job Order)"
        verbose_name_plural = "سفارش‌های کار"


class CalibrationResult(models.Model):
    """
    نتیجه نهایی کالیبراسیون شامل شرایط محیطی و وضعیت کلی
    """
    job_order = models.OneToOneField(JobOrder, on_delete=models.CASCADE, related_name='result', verbose_name="سفارش کار مرتبط")
    
    # شرایط محیطی (حیاتی برای استاندارد 17025)
    temperature = models.FloatField(verbose_name="دما (°C)", help_text="مثلاً 23.5")
    humidity = models.FloatField(verbose_name="رطوبت (%)", help_text="مثلاً 45")
    
    # ردیابی (Traceability): از چه تجهیز مرجعی استفاده شده؟
    reference_standard = models.ForeignKey(
        Equipment, 
        on_delete=models.PROTECT, 
        related_name='calibrations_performed',
        
        # *** تغییر مهم: فقط تجهیزات مرجع اینجا لیست شوند ***
        limit_choices_to={'category': 'REFERENCE'},
        
        verbose_name="تجهیز مرجع استفاده شده"
    )
    
    calibration_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ اجرا")
    
    technical_notes = models.TextField(blank=True, verbose_name="یادداشت فنی")
    
    # نتیجه نهایی که تکنسین اعلام می‌کند
    final_verdict = models.BooleanField(default=True, verbose_name="آیا قبول است؟ (Pass)")

    def __str__(self):
        return f"Result for {self.job_order.request.equipment.name}"

    class Meta:
        verbose_name = "نتیجه کالیبراسیون"
        verbose_name_plural = "نتایج کالیبراسیون"


class MeasurementResult(models.Model):
    """
    جدول ریز داده‌های اندازه‌گیری (سطر به سطر)
    """
    calibration_result = models.ForeignKey(CalibrationResult, on_delete=models.CASCADE, related_name='measurements')
    
    # مثلاً: نقطه 10 بار
    nominal_value = models.FloatField(verbose_name="مقدار مرجع/نمی (Nominal)")
    # دستگاه 10.1 نشان داد
    measured_value = models.FloatField(verbose_name="مقدار خوانده شده (Measured)")
    
    # خطا خودکار محاسبه نمی‌شود چون شاید تکنسین بخواهد دستی وارد کند، اما ما بعداً با کد پر می‌کنیم
    error = models.FloatField(verbose_name="خطا", blank=True, null=True)
    
    # محاسبه عدم قطعیت (بعداً پر می‌شود)
    uncertainty = models.FloatField(verbose_name="عدم قطعیت", blank=True, null=True)

    def save(self, *args, **kwargs):
        # محاسبه خودکار خطا هنگام ذخیره
        if self.measured_value is not None and self.nominal_value is not None:
            self.error = self.measured_value - self.nominal_value
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "داده اندازه‌گیری"
        verbose_name_plural = "داده‌های اندازه‌گیری"
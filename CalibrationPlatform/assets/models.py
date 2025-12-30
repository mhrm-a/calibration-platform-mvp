from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

# 1. مدل کاربر سفارشی
class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', _('مدیر سیستم')
        CUSTOMER = 'CUSTOMER', _('مشتری')
        TECHNICIAN = 'TECHNICIAN', _('تکنسین')
        QUALITY_MANAGER = 'QM', _('مدیر کیفی')

    role = models.CharField(
        max_length=20, 
        choices=Roles.choices, 
        default=Roles.CUSTOMER,
        verbose_name="نقش کاربر"
    )
    company_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="نام شرکت/سازمان")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

# 2. مدل تجهیزات
class Equipment(models.Model):
    # --- کلاس‌های انتخابی (Choices) ---
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('فعال')
        IN_CALIBRATION = 'IN_CAL', _('در حال کالیبراسیون')
        OUT_OF_SERVICE = 'OUT', _('خارج از سرویس')
        SCRAPPED = 'SCRAPPED', _('اسقاط شده')

    class Category(models.TextChoices):
        CUSTOMER_EQUIPMENT = 'CUSTOMER', _('تجهیز مشتری (تحت کالیبراسیون)')
        REFERENCE_STANDARD = 'REFERENCE', _('تجهیز مرجع (استاندارد آزمایشگاه)')

    # --- فیلدهای اصلی (این‌ها نباید پاک شوند) ---
    name = models.CharField(max_length=200, verbose_name="نام تجهیز")
    serial_number = models.CharField(max_length=100, unique=True, verbose_name="شماره سریال")
    manufacturer = models.CharField(max_length=100, verbose_name="سازنده", blank=True)
    model_number = models.CharField(max_length=100, verbose_name="مدل", blank=True)
    
    # ارتباط با مدل User (صاحب تجهیز)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equipments', verbose_name="مالک")
    
    # فیلد جدید دسته‌بندی
    category = models.CharField(
        max_length=20, 
        choices=Category.choices, 
        default=Category.CUSTOMER_EQUIPMENT,
        verbose_name="دسته تجهیز"
    )

    calibration_interval = models.IntegerField(default=365, help_text="تعداد روز", verbose_name="دوره تناوب")
    last_calibration_date = models.DateField(null=True, blank=True, verbose_name="آخرین کالیبراسیون")
    next_due_date = models.DateField(null=True, blank=True, verbose_name="تاریخ سررسید بعدی")
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name="وضعیت")

    # فیلد جادویی برای مشخصات فنی متغیر
    technical_specs = models.JSONField(default=dict, blank=True, verbose_name="مشخصات فنی (JSON)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.serial_number}"

    class Meta:
        verbose_name = "تجهیز"
        verbose_name_plural = "تجهیزات"
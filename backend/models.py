"""
backend/models.py
=================
Models for Smart Lecturer Review System.

Roles: admin | hod | lecturer | student
All role-specific data lives in UserProfile (OneToOne with Django User).
"""

from django.db import models
from django.contrib.auth.models import User


# ── Choice constants ──────────────────────────────────────────

ROLE_CHOICES = [
    ('admin',    'Admin'),
    ('hod',      'HOD'),
    ('lecturer', 'Lecturer'),
    ('student',  'Student'),
]

ATTENDANCE_STATUS = [
    ('present', 'Present'),
    ('absent',  'Absent'),
    ('late',    'Late'),
]

REVIEW_STATUS = [
    ('pending',  'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]

THEME_CHOICES = [
    ('light', 'Light'),
    ('dark',  'Dark'),
    ('blue',  'Blue'),
    ('green', 'Green'),
]


# ── Department ────────────────────────────────────────────────

class Department(models.Model):
    name       = models.CharField(max_length=100, unique=True)
    code       = models.CharField(max_length=10,  unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# ── UserProfile ───────────────────────────────────────────────

class UserProfile(models.Model):
    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role             = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    department       = models.ForeignKey(Department, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='users')
    phone            = models.CharField(max_length=20, blank=True, default='')
    address          = models.TextField(blank=True, default='')
    theme            = models.CharField(max_length=20, choices=THEME_CHOICES, default='light')
    is_primary_admin = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    def get_full_name(self):
        n = self.user.get_full_name()
        return n if n.strip() else self.user.username


# ── Subject ───────────────────────────────────────────────────

class Subject(models.Model):
    name       = models.CharField(max_length=200)
    code       = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='subjects')
    semester   = models.PositiveIntegerField(default=1)
    credits    = models.PositiveIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['department', 'semester', 'name']

    def __str__(self):
        return f"{self.code} — {self.name}"


# ── Lecturer ──────────────────────────────────────────────────

class Lecturer(models.Model):
    user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lecturer_profile')
    department     = models.ForeignKey(Department, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='lecturers')
    employee_id    = models.CharField(max_length=50, unique=True, blank=True, default='')
    designation    = models.CharField(max_length=100, blank=True, default='')
    subjects       = models.ManyToManyField(Subject, blank=True, related_name='lecturers')
    average_rating = models.FloatField(default=0.0)
    total_reviews  = models.PositiveIntegerField(default=0)
    is_active      = models.BooleanField(default=True)
    joined_date    = models.DateField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f"Lecturer: {self.user.get_full_name() or self.user.username}"

    def update_rating(self):
        reviews = self.reviews.filter(status='approved')
        if reviews.exists():
            from django.db.models import Avg
            self.average_rating = reviews.aggregate(avg=Avg('overall_rating'))['avg'] or 0.0
            self.total_reviews  = reviews.count()
        else:
            self.average_rating = 0.0
            self.total_reviews  = 0
        self.save(update_fields=['average_rating', 'total_reviews'])


# ── HOD ───────────────────────────────────────────────────────

class HOD(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='hod_profile')
    department  = models.ForeignKey(Department, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='hods')
    employee_id = models.CharField(max_length=50, unique=True, blank=True, default='')
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'HOD'
        ordering     = ['department__name']

    def __str__(self):
        return f"HOD: {self.user.get_full_name() or self.user.username}"


# ── Student ───────────────────────────────────────────────────

class Student(models.Model):
    user          = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    department    = models.ForeignKey(Department, on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='students')
    roll_number   = models.CharField(max_length=50, unique=True, blank=True, default='')
    semester      = models.PositiveIntegerField(default=1)
    subjects      = models.ManyToManyField(Subject, blank=True, related_name='students')
    is_active     = models.BooleanField(default=True)
    admitted_year = models.PositiveIntegerField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['department__name', 'semester', 'roll_number']

    def __str__(self):
        return f"Student: {self.user.get_full_name() or self.user.username} ({self.roll_number})"

    def attendance_percentage(self, subject=None):
        qs = self.attendance_records.all()
        if subject:
            qs = qs.filter(subject=subject)
        total = qs.count()
        if total == 0:
            return 0.0
        return round(qs.filter(status='present').count() / total * 100, 2)


# ── StudentAttendance ─────────────────────────────────────────

class StudentAttendance(models.Model):
    student    = models.ForeignKey(Student,  on_delete=models.CASCADE,
                                   related_name='attendance_records')
    subject    = models.ForeignKey(Subject,  on_delete=models.CASCADE,
                                   related_name='attendance_records')
    lecturer   = models.ForeignKey(Lecturer, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='marked_attendance')
    date       = models.DateField()
    status     = models.CharField(max_length=10, choices=ATTENDANCE_STATUS, default='present')
    remarks    = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering        = ['-date', 'student__roll_number']
        unique_together = ['student', 'subject', 'date']
        verbose_name    = 'Student Attendance'

    def __str__(self):
        return f"{self.student.user.username} | {self.subject.code} | {self.date} | {self.status}"


# ── LecturerReview ────────────────────────────────────────────

class LecturerReview(models.Model):
    lecturer         = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='reviews')
    student          = models.ForeignKey(Student,  on_delete=models.CASCADE, related_name='submitted_reviews')
    subject          = models.ForeignKey(Subject,  on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='reviews')
    teaching_quality = models.PositiveIntegerField(default=3)
    communication    = models.PositiveIntegerField(default=3)
    punctuality      = models.PositiveIntegerField(default=3)
    knowledge        = models.PositiveIntegerField(default=3)
    overall_rating   = models.FloatField(default=3.0)
    feedback         = models.TextField(blank=True, default='')
    is_anonymous     = models.BooleanField(default=False)
    status           = models.CharField(max_length=20, choices=REVIEW_STATUS, default='pending')
    rejection_reason = models.TextField(blank=True, default='')
    submitted_at     = models.DateTimeField(auto_now_add=True)
    reviewed_at      = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering     = ['-submitted_at']
        verbose_name = 'Lecturer Review'

    def __str__(self):
        return (f"Review: {self.student.user.username} → "
                f"{self.lecturer.user.username} ({self.overall_rating}★)")

    def save(self, *args, **kwargs):
        self.overall_rating = round(
            (self.teaching_quality + self.communication +
             self.punctuality + self.knowledge) / 4, 2
        )
        super().save(*args, **kwargs)
        self.lecturer.update_rating()


# ── ActivityLog ───────────────────────────────────────────────

LOG_TYPE_CHOICES = [
    ('login',             'Login'),
    ('logout',            'Logout'),
    ('review_submitted',  'Review Submitted'),
    ('review_rejected',   'Review Rejected'),
    ('attendance_marked', 'Attendance Marked'),
    ('user_created',      'User Created'),
    ('profile_updated',   'Profile Updated'),
    ('other',             'Other'),
]


class ActivityLog(models.Model):
    user        = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='activity_logs')
    log_type    = models.CharField(max_length=50, choices=LOG_TYPE_CHOICES, default='other')
    description = models.TextField()
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    extra_data  = models.JSONField(default=dict, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering     = ['-created_at']
        verbose_name = 'Activity Log'

    def __str__(self):
        u = self.user.username if self.user else 'anon'
        return f"[{self.log_type}] {u}: {self.description[:60]}"


# ── BadWord ───────────────────────────────────────────────────

class BadWord(models.Model):
    word       = models.CharField(max_length=100, unique=True)
    added_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['word']

    def __str__(self):
        return self.word

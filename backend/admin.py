"""
backend/admin.py
================
Django Admin panel registration.
Access at: http://localhost:8000/admin/
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone

from .models import (
    Department, UserProfile, Subject, Lecturer, HOD,
    Student, StudentAttendance, LecturerReview, ActivityLog, BadWord
)


# ── Inline: show UserProfile inside User admin page ───────────

class UserProfileInline(admin.StackedInline):
    model      = UserProfile
    can_delete = False
    fields     = ['role', 'department', 'phone', 'address', 'theme', 'is_primary_admin']
    extra      = 0


class CustomUserAdmin(BaseUserAdmin):
    inlines      = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_role', 'is_active']
    list_filter  = ['is_active', 'is_staff', 'profile__role', 'profile__department']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def get_role(self, obj):
        try:    return obj.profile.role
        except: return '—'
    get_role.short_description = 'Role'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ── Department ────────────────────────────────────────────────

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']


# ── UserProfile ───────────────────────────────────────────────

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'role', 'department', 'phone', 'is_primary_admin']
    list_filter   = ['role', 'department']
    search_fields = ['user__username', 'user__email']
    actions       = ['release_admin_lock']

    def release_admin_lock(self, request, queryset):
        n = queryset.filter(role='admin').update(is_primary_admin=False)
        self.message_user(request, f"Released admin lock for {n} user(s).")
    release_admin_lock.short_description = "Release admin session lock"


# ── Subject ───────────────────────────────────────────────────

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display  = ['code', 'name', 'department', 'semester', 'credits']
    list_filter   = ['department', 'semester']
    search_fields = ['name', 'code']


# ── Lecturer ──────────────────────────────────────────────────

@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display      = ['user', 'department', 'designation', 'average_rating', 'total_reviews', 'is_active']
    list_filter       = ['department', 'is_active']
    search_fields     = ['user__username', 'user__first_name', 'user__last_name', 'employee_id']
    filter_horizontal = ['subjects']
    readonly_fields   = ['average_rating', 'total_reviews', 'created_at']


# ── HOD ───────────────────────────────────────────────────────

@admin.register(HOD)
class HODAdmin(admin.ModelAdmin):
    list_display  = ['user', 'department', 'employee_id', 'is_active']
    list_filter   = ['department']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']


# ── Student ───────────────────────────────────────────────────

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display      = ['user', 'department', 'roll_number', 'semester', 'is_active']
    list_filter       = ['department', 'semester', 'is_active']
    search_fields     = ['user__username', 'user__first_name', 'roll_number']
    filter_horizontal = ['subjects']
    readonly_fields   = ['created_at']


# ── StudentAttendance ─────────────────────────────────────────

@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display   = ['student', 'subject', 'date', 'status', 'lecturer', 'created_at']
    list_filter    = ['status', 'date', 'subject__department']
    search_fields  = ['student__user__username', 'subject__name']
    date_hierarchy = 'date'
    ordering       = ['-date']


# ── LecturerReview ────────────────────────────────────────────

@admin.register(LecturerReview)
class LecturerReviewAdmin(admin.ModelAdmin):
    list_display    = ['lecturer', 'student', 'overall_rating', 'status', 'is_anonymous', 'submitted_at']
    list_filter     = ['status', 'is_anonymous', 'lecturer__department']
    search_fields   = ['lecturer__user__username', 'student__user__username', 'feedback']
    readonly_fields = ['overall_rating', 'submitted_at']
    date_hierarchy  = 'submitted_at'
    actions         = ['approve_reviews', 'reject_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(status='approved', reviewed_at=timezone.now())
        for r in queryset:
            r.lecturer.update_rating()
        self.message_user(request, f"Approved {queryset.count()} review(s).")
    approve_reviews.short_description = "✅ Approve selected reviews"

    def reject_reviews(self, request, queryset):
        queryset.update(
            status='rejected',
            reviewed_at=timezone.now(),
            rejection_reason='Rejected via admin panel.'
        )
        self.message_user(request, f"Rejected {queryset.count()} review(s).")
    reject_reviews.short_description = "❌ Reject selected reviews"


# ── ActivityLog ───────────────────────────────────────────────

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display    = ['user', 'log_type', 'description', 'ip_address', 'created_at']
    list_filter     = ['log_type', 'created_at']
    search_fields   = ['user__username', 'description']
    readonly_fields = ['created_at', 'ip_address', 'extra_data']
    date_hierarchy  = 'created_at'

    def has_add_permission(self, request):
        return False   # logs are system-generated only


# ── BadWord ───────────────────────────────────────────────────

@admin.register(BadWord)
class BadWordAdmin(admin.ModelAdmin):
    list_display  = ['word', 'added_by', 'created_at']
    search_fields = ['word']
    readonly_fields = ['created_at']


# ── Admin site branding ───────────────────────────────────────

admin.site.site_header  = "Smart Lecturer Review System"
admin.site.site_title   = "SLRS Admin"
admin.site.index_title  = "Administration Panel"

"""
backend/urls.py
===============
URL patterns for all 19 views.
Included from root urls.py as: path('', include('backend.urls'))
"""

from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────
    path('',          views.login_view,    name='home'),
    path('login/',    views.login_view,    name='login'),
    path('logout/',   views.logout_view,   name='logout'),
    path('register/', views.register_view, name='register'),

    # ── Dashboard dispatcher ──────────────────────────────────
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # ── Student ───────────────────────────────────────────────
    path('student-dashboard/',      views.student_dashboard,      name='student_dashboard'),
    path('student-attendance/',     views.student_attendance,      name='student_attendance'),
    path('student-review/',         views.student_review,          name='student_review'),
    path('student-review-history/', views.student_review_history,  name='student_review_history'),

    # ── Lecturer ──────────────────────────────────────────────
    path('lecturer-dashboard/',  views.lecturer_dashboard,  name='lecturer_dashboard'),
    path('lecturer-attendance/', views.lecturer_attendance, name='lecturer_attendance'),
    path('lecturer-reviews/',    views.lecturer_reviews,    name='lecturer_reviews'),

    # ── HOD ───────────────────────────────────────────────────
    path('hod-dashboard/',         views.hod_dashboard,         name='hod_dashboard'),
    path('hod-manage-students/',   views.hod_manage_students,   name='hod_manage_students'),
    path('hod-manage-lecturers/',  views.hod_manage_lecturers,  name='hod_manage_lecturers'),
    path('hod-reviews/',           views.hod_reviews,           name='hod_reviews'),

    # ── Admin ─────────────────────────────────────────────────
    path('admin-dashboard/',    views.admin_dashboard,    name='admin_dashboard'),
    path('admin-manage-users/', views.admin_manage_users, name='admin_manage_users'),
    path('admin-activity-logs/', views.admin_activity_logs, name='admin_activity_logs'),
    path('admin-bad-words/',    views.admin_bad_words,    name='admin_bad_words'),

    # ── Settings ──────────────────────────────────────────────
    path('settings/', views.settings_view, name='settings'),
]

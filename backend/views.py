"""
backend/views.py
================
All Django views — one per HTML template.

Template ↔ View mapping (19 templates):
  login.html                → login_view
  register.html             → register_view
  dashboard.html            → dashboard_view          (role dispatcher)
  student_dashboard.html    → student_dashboard
  student_attendance.html   → student_attendance
  student_review.html       → student_review
  student_review_history.html → student_review_history
  lecturer_dashboard.html   → lecturer_dashboard
  lecturer_attendance.html  → lecturer_attendance
  lecturer_reviews.html     → lecturer_reviews
  hod_dashboard.html        → hod_dashboard
  hod_manage_students.html  → hod_manage_students
  hod_manage_lecturers.html → hod_manage_lecturers
  hod_reviews.html          → hod_reviews
  admin_dashboard.html      → admin_dashboard
  admin_manage_users.html   → admin_manage_users
  admin_activity_logs.html  → admin_activity_logs
  admin_bad_words.html      → admin_bad_words
  settings.html             → settings_view
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Count

from .models import (
    UserProfile, Department, Subject, Lecturer, HOD,
    Student, StudentAttendance, LecturerReview, ActivityLog, BadWord
)
from .forms import (
    LoginForm, RegisterForm, ProfileUpdateForm, ChangePasswordForm,
    MarkAttendanceForm, SubmitReviewForm,
    AddUserForm, ReviewModerationForm, BadWordForm,
)
from .decorators import admin_required, hod_required, lecturer_required, student_required
from .utils import log_activity, create_user_with_role, get_dashboard_url, get_attendance_summary


# ══════════════════════════════════════════════════════════════
# AUTH VIEWS
# ══════════════════════════════════════════════════════════════

def login_view(request):
    """GET/POST → login.html"""
    if request.user.is_authenticated:
        return redirect(get_dashboard_url(request.user))

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()

            # Admin single-session lock
            try:
                profile = user.profile
                if profile.role == 'admin':
                    other_locked = UserProfile.objects.filter(
                        role='admin', is_primary_admin=True
                    ).exclude(user=user).exists()
                    if other_locked:
                        messages.error(
                            request,
                            "Admin access restricted — another admin session is already active."
                        )
                        return render(request, 'login.html', {'form': form})
                    profile.is_primary_admin = True
                    profile.save(update_fields=['is_primary_admin'])
            except UserProfile.DoesNotExist:
                pass

            login(request, user)
            log_activity(user, 'login', f"User '{user.username}' logged in.", request)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect(get_dashboard_url(user))
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'login.html', {'form': form})


def register_view(request):
    """GET/POST → register.html"""
    if request.user.is_authenticated:
        return redirect(get_dashboard_url(request.user))

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        try:
            user = create_user_with_role(
                username   = cd['username'],
                email      = cd['email'],
                password   = cd['password1'],
                role       = cd['role'],
                first_name = cd.get('first_name', ''),
                last_name  = cd.get('last_name', ''),
                department = cd.get('department'),
                phone      = cd.get('phone', ''),
            )
            log_activity(user, 'user_created',
                         f"New user '{user.username}' registered as '{cd['role']}'.", request)
            login(request, user)
            messages.success(request, "Account created successfully. Welcome!")
            return redirect(get_dashboard_url(user))
        except ValueError as e:
            messages.error(request, str(e))

    return render(request, 'register.html', {'form': form})


@login_required
def logout_view(request):
    """POST → logout → redirect to login.html"""
    try:
        profile = request.user.profile
        if profile.role == 'admin' and profile.is_primary_admin:
            profile.is_primary_admin = False
            profile.save(update_fields=['is_primary_admin'])
    except UserProfile.DoesNotExist:
        pass

    log_activity(request.user, 'logout', f"User '{request.user.username}' logged out.", request)
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


# ══════════════════════════════════════════════════════════════
# DASHBOARD DISPATCHER
# ══════════════════════════════════════════════════════════════

@login_required
def dashboard_view(request):
    """Redirects to the role-appropriate dashboard."""
    return redirect(get_dashboard_url(request.user))


# ══════════════════════════════════════════════════════════════
# STUDENT VIEWS
# ══════════════════════════════════════════════════════════════

@student_required
def student_dashboard(request):
    """GET → student_dashboard.html"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('login')

    attendance_summary = get_attendance_summary(student)
    recent_reviews = LecturerReview.objects.filter(
        student=student
    ).select_related('lecturer__user', 'subject').order_by('-submitted_at')[:5]

    overall_pct = 0.0
    if attendance_summary:
        overall_pct = round(
            sum(v['percentage'] for v in attendance_summary.values()) / len(attendance_summary), 1
        )

    context = {
        'student':            student,
        'attendance_summary': attendance_summary,
        'recent_reviews':     recent_reviews,
        'overall_pct':        overall_pct,
        'total_subjects':     student.subjects.count(),
    }
    return render(request, 'student_dashboard.html', context)


@student_required
def student_attendance(request):
    """GET → student_attendance.html"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        return redirect('login')

    subject_filter = request.GET.get('subject')
    records = student.attendance_records.select_related('subject', 'lecturer__user').order_by('-date')
    if subject_filter:
        records = records.filter(subject_id=subject_filter)

    attendance_summary = get_attendance_summary(student)
    subjects = student.subjects.all()

    context = {
        'student':            student,
        'records':            records,
        'attendance_summary': attendance_summary,
        'subjects':           subjects,
        'selected_subject':   subject_filter,
    }
    return render(request, 'student_attendance.html', context)


@student_required
def student_review(request):
    """GET/POST → student_review.html"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        return redirect('login')

    # Filter lecturers to same department
    dept_lecturers = Lecturer.objects.filter(
        department=student.department, is_active=True
    ).select_related('user') if student.department else Lecturer.objects.filter(is_active=True)

    form = SubmitReviewForm(request.POST or None)
    # Limit lecturer choices to department
    form.fields['lecturer'].queryset = dept_lecturers

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        review = LecturerReview.objects.create(
            lecturer         = cd['lecturer'],
            student          = student,
            subject          = cd.get('subject'),
            teaching_quality = int(cd['teaching_quality']),
            communication    = int(cd['communication']),
            punctuality      = int(cd['punctuality']),
            knowledge        = int(cd['knowledge']),
            feedback         = cd.get('feedback', ''),
            is_anonymous     = cd.get('is_anonymous', False),
            status           = 'pending',
        )
        log_activity(request.user, 'review_submitted',
                     f"Review submitted for {cd['lecturer'].user.username}.", request)
        messages.success(request, "Your review has been submitted and is pending approval.")
        return redirect('student_review_history')

    context = {
        'form':     form,
        'student':  student,
        'lecturers': dept_lecturers,
    }
    return render(request, 'student_review.html', context)


@student_required
def student_review_history(request):
    """GET → student_review_history.html"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        return redirect('login')

    reviews = LecturerReview.objects.filter(
        student=student
    ).select_related('lecturer__user', 'subject').order_by('-submitted_at')

    context = {'student': student, 'reviews': reviews}
    return render(request, 'student_review_history.html', context)


# ══════════════════════════════════════════════════════════════
# LECTURER VIEWS
# ══════════════════════════════════════════════════════════════

@lecturer_required
def lecturer_dashboard(request):
    """GET → lecturer_dashboard.html"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        messages.error(request, "Lecturer profile not found.")
        return redirect('login')

    students_in_dept = Student.objects.filter(
        department=lecturer.department, is_active=True
    ).count() if lecturer.department else 0

    recent_reviews = LecturerReview.objects.filter(
        lecturer=lecturer, status='approved'
    ).select_related('student__user', 'subject').order_by('-submitted_at')[:5]

    today = timezone.now().date()
    today_attendance_count = StudentAttendance.objects.filter(
        lecturer=lecturer, date=today
    ).count()

    context = {
        'lecturer':               lecturer,
        'students_in_dept':       students_in_dept,
        'recent_reviews':         recent_reviews,
        'today_attendance_count': today_attendance_count,
        'total_subjects':         lecturer.subjects.count(),
    }
    return render(request, 'lecturer_dashboard.html', context)


@lecturer_required
def lecturer_attendance(request):
    """GET/POST → lecturer_attendance.html"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        return redirect('login')

    form         = MarkAttendanceForm(request.POST or None)
    form.fields['subject'].queryset = lecturer.subjects.all()
    attendance_list = []
    selected_subject = None
    selected_date    = None

    if request.method == 'POST' and 'mark' in request.POST:
        # Bulk attendance marking
        subject_id   = request.POST.get('subject')
        date_str     = request.POST.get('date')
        student_ids  = request.POST.getlist('student_ids')
        statuses     = request.POST.getlist('status')

        try:
            subject = Subject.objects.get(pk=subject_id)
            from datetime import date
            mark_date = date.fromisoformat(date_str)
            created_count = 0
            for sid, st in zip(student_ids, statuses):
                student = Student.objects.get(pk=sid)
                obj, created = StudentAttendance.objects.update_or_create(
                    student=student, subject=subject, date=mark_date,
                    defaults={'status': st, 'lecturer': lecturer}
                )
                if created:
                    created_count += 1
            log_activity(request.user, 'attendance_marked',
                         f"Marked attendance for {subject.name} on {mark_date}.", request)
            messages.success(request, f"Attendance saved for {subject.name} on {mark_date}.")
        except Exception as e:
            messages.error(request, f"Error saving attendance: {e}")

    elif request.method == 'POST' and form.is_valid():
        cd             = form.cleaned_data
        selected_subject = cd['subject']
        selected_date    = cd['date']
        # Load students enrolled in this subject
        attendance_list = []
        for student in selected_subject.students.filter(is_active=True):
            existing = StudentAttendance.objects.filter(
                student=student, subject=selected_subject, date=selected_date
            ).first()
            attendance_list.append({
                'student':  student,
                'existing': existing,
                'status':   existing.status if existing else 'present',
            })

    recent = StudentAttendance.objects.filter(
        lecturer=lecturer
    ).select_related('student__user', 'subject').order_by('-date')[:20]

    context = {
        'form':             form,
        'attendance_list':  attendance_list,
        'selected_subject': selected_subject,
        'selected_date':    selected_date,
        'recent':           recent,
        'lecturer':         lecturer,
    }
    return render(request, 'lecturer_attendance.html', context)


@lecturer_required
def lecturer_reviews(request):
    """GET → lecturer_reviews.html — lecturer sees their own approved reviews"""
    try:
        lecturer = request.user.lecturer_profile
    except Lecturer.DoesNotExist:
        return redirect('login')

    reviews = LecturerReview.objects.filter(
        lecturer=lecturer, status='approved'
    ).select_related('student__user', 'subject').order_by('-submitted_at')

    avg_ratings = reviews.aggregate(
        avg_teaching  = Avg('teaching_quality'),
        avg_comm      = Avg('communication'),
        avg_punctual  = Avg('punctuality'),
        avg_knowledge = Avg('knowledge'),
        avg_overall   = Avg('overall_rating'),
    )

    context = {
        'lecturer':    lecturer,
        'reviews':     reviews,
        'avg_ratings': avg_ratings,
    }
    return render(request, 'lecturer_reviews.html', context)


# ══════════════════════════════════════════════════════════════
# HOD VIEWS
# ══════════════════════════════════════════════════════════════

@hod_required
def hod_dashboard(request):
    """GET → hod_dashboard.html"""
    try:
        hod = request.user.hod_profile
    except HOD.DoesNotExist:
        messages.error(request, "HOD profile not found.")
        return redirect('login')

    dept = hod.department
    students_count  = Student.objects.filter(department=dept, is_active=True).count() if dept else 0
    lecturers_count = Lecturer.objects.filter(department=dept, is_active=True).count() if dept else 0
    pending_reviews = LecturerReview.objects.filter(
        lecturer__department=dept, status='pending'
    ).count() if dept else 0

    top_lecturers = Lecturer.objects.filter(
        department=dept, is_active=True
    ).order_by('-average_rating')[:5] if dept else []

    context = {
        'hod':              hod,
        'students_count':   students_count,
        'lecturers_count':  lecturers_count,
        'pending_reviews':  pending_reviews,
        'top_lecturers':    top_lecturers,
    }
    return render(request, 'hod_dashboard.html', context)


@hod_required
def hod_manage_students(request):
    """GET/POST → hod_manage_students.html"""
    try:
        hod = request.user.hod_profile
    except HOD.DoesNotExist:
        return redirect('login')

    form = AddUserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        try:
            user = create_user_with_role(
                username   = cd['username'],
                email      = cd['email'],
                password   = cd['password'],
                role       = cd['role'],
                first_name = cd.get('first_name', ''),
                last_name  = cd.get('last_name', ''),
                department = cd.get('department') or hod.department,
            )
            log_activity(request.user, 'user_created',
                         f"HOD created user '{user.username}' ({cd['role']}).", request)
            messages.success(request, f"User '{user.username}' created successfully.")
            return redirect('hod_manage_students')
        except ValueError as e:
            messages.error(request, str(e))

    students = Student.objects.filter(
        department=hod.department, is_active=True
    ).select_related('user').order_by('roll_number') if hod.department else []

    context = {
        'hod':      hod,
        'students': students,
        'form':     form,
    }
    return render(request, 'hod_manage_students.html', context)


@hod_required
def hod_manage_lecturers(request):
    """GET → hod_manage_lecturers.html"""
    try:
        hod = request.user.hod_profile
    except HOD.DoesNotExist:
        return redirect('login')

    lecturers = Lecturer.objects.filter(
        department=hod.department, is_active=True
    ).select_related('user').prefetch_related('subjects') if hod.department else []

    context = {'hod': hod, 'lecturers': lecturers}
    return render(request, 'hod_manage_lecturers.html', context)


@hod_required
def hod_reviews(request):
    """GET/POST → hod_reviews.html — approve/reject pending reviews"""
    try:
        hod = request.user.hod_profile
    except HOD.DoesNotExist:
        return redirect('login')

    if request.method == 'POST':
        review_id = request.POST.get('review_id')
        action    = request.POST.get('action')
        reason    = request.POST.get('rejection_reason', '')

        review = get_object_or_404(LecturerReview, pk=review_id,
                                   lecturer__department=hod.department)
        if action == 'approve':
            review.status      = 'approved'
            review.reviewed_at = timezone.now()
            review.rejection_reason = ''
            review.save()
            messages.success(request, "Review approved.")
        elif action == 'reject':
            if not reason:
                messages.error(request, "Please provide a rejection reason.")
            else:
                review.status           = 'rejected'
                review.reviewed_at      = timezone.now()
                review.rejection_reason = reason
                review.save()
                log_activity(request.user, 'review_rejected',
                             f"Review {review.id} rejected. Reason: {reason}", request)
                messages.success(request, "Review rejected.")
        return redirect('hod_reviews')

    pending  = LecturerReview.objects.filter(
        lecturer__department=hod.department, status='pending'
    ).select_related('lecturer__user', 'student__user', 'subject').order_by('-submitted_at')

    approved = LecturerReview.objects.filter(
        lecturer__department=hod.department, status='approved'
    ).select_related('lecturer__user', 'student__user', 'subject').order_by('-submitted_at')[:20]

    context = {
        'hod':      hod,
        'pending':  pending,
        'approved': approved,
    }
    return render(request, 'hod_reviews.html', context)


# ══════════════════════════════════════════════════════════════
# ADMIN VIEWS
# ══════════════════════════════════════════════════════════════

@admin_required
def admin_dashboard(request):
    """GET → admin_dashboard.html"""
    total_users     = UserProfile.objects.count()
    total_students  = Student.objects.count()
    total_lecturers = Lecturer.objects.count()
    total_hods      = HOD.objects.count()
    total_reviews   = LecturerReview.objects.count()
    pending_reviews = LecturerReview.objects.filter(status='pending').count()

    recent_logs = ActivityLog.objects.select_related('user').order_by('-created_at')[:10]

    reviews_by_dept = (
        LecturerReview.objects
        .filter(status='approved')
        .values('lecturer__department__name')
        .annotate(count=Count('id'), avg_rating=Avg('overall_rating'))
        .order_by('-count')
    )

    context = {
        'total_users':     total_users,
        'total_students':  total_students,
        'total_lecturers': total_lecturers,
        'total_hods':      total_hods,
        'total_reviews':   total_reviews,
        'pending_reviews': pending_reviews,
        'recent_logs':     recent_logs,
        'reviews_by_dept': reviews_by_dept,
    }
    return render(request, 'admin_dashboard.html', context)


@admin_required
def admin_manage_users(request):
    """GET/POST → admin_manage_users.html"""
    form = AddUserForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        try:
            user = create_user_with_role(
                username   = cd['username'],
                email      = cd['email'],
                password   = cd['password'],
                role       = cd['role'],
                first_name = cd.get('first_name', ''),
                last_name  = cd.get('last_name', ''),
                department = cd.get('department'),
            )
            log_activity(request.user, 'user_created',
                         f"Admin created user '{user.username}' ({cd['role']}).", request)
            messages.success(request, f"User '{user.username}' created successfully.")
            return redirect('admin_manage_users')
        except ValueError as e:
            messages.error(request, str(e))

    role_filter = request.GET.get('role', '')
    dept_filter = request.GET.get('department', '')

    profiles = UserProfile.objects.select_related('user', 'department').order_by('-created_at')
    if role_filter:
        profiles = profiles.filter(role=role_filter)
    if dept_filter:
        profiles = profiles.filter(department_id=dept_filter)

    context = {
        'form':        form,
        'profiles':    profiles,
        'departments': Department.objects.all(),
        'role_filter': role_filter,
        'dept_filter': dept_filter,
    }
    return render(request, 'admin_manage_users.html', context)


@admin_required
def admin_activity_logs(request):
    """GET → admin_activity_logs.html"""
    log_type_filter = request.GET.get('log_type', '')
    username_filter = request.GET.get('username', '')

    logs = ActivityLog.objects.select_related('user').order_by('-created_at')
    if log_type_filter:
        logs = logs.filter(log_type=log_type_filter)
    if username_filter:
        logs = logs.filter(user__username__icontains=username_filter)

    from .models import LOG_TYPE_CHOICES
    context = {
        'logs':             logs[:200],
        'log_type_choices': LOG_TYPE_CHOICES,
        'log_type_filter':  log_type_filter,
        'username_filter':  username_filter,
    }
    return render(request, 'admin_activity_logs.html', context)


@admin_required
def admin_bad_words(request):
    """GET/POST → admin_bad_words.html"""
    form = BadWordForm(request.POST or None)

    if request.method == 'POST':
        if 'delete' in request.POST:
            word_id = request.POST.get('word_id')
            BadWord.objects.filter(pk=word_id).delete()
            messages.success(request, "Word removed from blocklist.")
            return redirect('admin_bad_words')

        if form.is_valid():
            word = form.save(commit=False)
            word.added_by = request.user
            word.save()
            messages.success(request, f"'{word.word}' added to blocklist.")
            return redirect('admin_bad_words')

    bad_words = BadWord.objects.select_related('added_by').order_by('word')
    context = {'form': form, 'bad_words': bad_words}
    return render(request, 'admin_bad_words.html', context)


# ══════════════════════════════════════════════════════════════
# SETTINGS VIEW
# ══════════════════════════════════════════════════════════════

@login_required
def settings_view(request):
    """GET/POST → settings.html"""
    profile = request.user.profile
    profile_form  = ProfileUpdateForm(initial={
        'first_name': request.user.first_name,
        'last_name':  request.user.last_name,
        'email':      request.user.email,
        'phone':      profile.phone,
        'address':    profile.address,
        'theme':      profile.theme,
    })
    password_form = ChangePasswordForm()

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST)
            if profile_form.is_valid():
                cd = profile_form.cleaned_data
                request.user.first_name = cd.get('first_name', '')
                request.user.last_name  = cd.get('last_name', '')
                request.user.email      = cd.get('email', '')
                request.user.save()
                profile.phone   = cd.get('phone', '')
                profile.address = cd.get('address', '')
                profile.theme   = cd.get('theme', 'light')
                profile.save()
                log_activity(request.user, 'profile_updated',
                             f"User '{request.user.username}' updated their profile.", request)
                messages.success(request, "Profile updated successfully.")
                return redirect('settings')

        elif 'change_password' in request.POST:
            password_form = ChangePasswordForm(request.POST)
            if password_form.is_valid():
                cd = password_form.cleaned_data
                if request.user.check_password(cd['old_password']):
                    request.user.set_password(cd['new_password1'])
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    messages.success(request, "Password changed successfully.")
                else:
                    messages.error(request, "Old password is incorrect.")
                return redirect('settings')

    context = {
        'profile_form':  profile_form,
        'password_form': password_form,
        'profile':       profile,
    }
    return render(request, 'settings.html', context)

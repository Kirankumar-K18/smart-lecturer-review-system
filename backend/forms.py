"""
backend/forms.py
================
Django Forms for all frontend templates.
Each form corresponds to exactly one HTML template's <form> element.
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import (
    UserProfile, Department, Subject, Lecturer,
    HOD, Student, StudentAttendance, LecturerReview, BadWord
)


# ── Auth Forms ────────────────────────────────────────────────

class LoginForm(AuthenticationForm):
    """Used by login.html"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Username or Email', 'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'placeholder': 'Password'
        })
    )


class RegisterForm(forms.Form):
    """Used by register.html"""
    ROLE_OPTIONS = [
        ('student',  'Student'),
        ('lecturer', 'Lecturer'),
        ('hod',      'HOD'),
    ]

    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name  = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    username   = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email      = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password1  = forms.CharField(label='Password',
                                  widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2  = forms.CharField(label='Confirm Password',
                                  widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    role       = forms.ChoiceField(choices=ROLE_OPTIONS,
                                    widget=forms.Select(attrs={'class': 'form-select'}))
    department = forms.ModelChoiceField(queryset=Department.objects.all(),
                                         widget=forms.Select(attrs={'class': 'form-select'}),
                                         required=False)
    phone      = forms.CharField(max_length=20, required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


# ── Profile / Settings Forms ──────────────────────────────────

class ProfileUpdateForm(forms.Form):
    """Used by settings.html"""
    first_name = forms.CharField(max_length=150, required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name  = forms.CharField(max_length=150, required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    email      = forms.EmailField(required=False,
                                   widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone      = forms.CharField(max_length=20, required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    address    = forms.CharField(required=False,
                                  widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    theme      = forms.ChoiceField(
        choices=[('light', 'Light'), ('dark', 'Dark'), ('blue', 'Blue'), ('green', 'Green')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )


class ChangePasswordForm(forms.Form):
    """Used by settings.html (password section)"""
    old_password  = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(label='New Password',
                                     widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(label='Confirm New Password',
                                     widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("New passwords do not match.")
        return cleaned


# ── Attendance Forms ──────────────────────────────────────────

class MarkAttendanceForm(forms.Form):
    """Used by lecturer_attendance.html — lecturer marks attendance for a class"""
    subject  = forms.ModelChoiceField(queryset=Subject.objects.all(),
                                       widget=forms.Select(attrs={'class': 'form-select'}))
    date     = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))


class AttendanceEntryForm(forms.ModelForm):
    """Single attendance record for one student (used in formset)"""
    class Meta:
        model  = StudentAttendance
        fields = ['student', 'subject', 'date', 'status', 'remarks']
        widgets = {
            'status':  forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }


# ── Review Forms ──────────────────────────────────────────────

class SubmitReviewForm(forms.Form):
    """Used by student_review.html"""
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    lecturer         = forms.ModelChoiceField(
        queryset=Lecturer.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    subject          = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    teaching_quality = forms.ChoiceField(choices=RATING_CHOICES,
                                          widget=forms.Select(attrs={'class': 'form-select'}))
    communication    = forms.ChoiceField(choices=RATING_CHOICES,
                                          widget=forms.Select(attrs={'class': 'form-select'}))
    punctuality      = forms.ChoiceField(choices=RATING_CHOICES,
                                          widget=forms.Select(attrs={'class': 'form-select'}))
    knowledge        = forms.ChoiceField(choices=RATING_CHOICES,
                                          widget=forms.Select(attrs={'class': 'form-select'}))
    feedback         = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                      'placeholder': 'Write your feedback here…'})
    )
    is_anonymous     = forms.BooleanField(required=False,
                                           widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    def clean_feedback(self):
        feedback = self.cleaned_data.get('feedback', '')
        if not feedback:
            return feedback
        bad_words = BadWord.objects.values_list('word', flat=True)
        lower_fb  = feedback.lower()
        for word in bad_words:
            if word.lower() in lower_fb:
                raise forms.ValidationError(
                    "Your feedback contains inappropriate language. Please revise."
                )
        return feedback


# ── HOD / Admin Management Forms ─────────────────────────────

class AddUserForm(forms.Form):
    """Used by hod_manage_students.html and admin_manage_users.html"""
    ROLE_OPTIONS = [
        ('student',  'Student'),
        ('lecturer', 'Lecturer'),
        ('hod',      'HOD'),
    ]
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name  = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    username   = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email      = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password   = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    role       = forms.ChoiceField(choices=ROLE_OPTIONS,
                                    widget=forms.Select(attrs={'class': 'form-select'}))
    department = forms.ModelChoiceField(queryset=Department.objects.all(),
                                         widget=forms.Select(attrs={'class': 'form-select'}),
                                         required=False)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already taken.")
        return username


class ReviewModerationForm(forms.Form):
    """Used by hod_reviews.html — approve or reject a review"""
    ACTION_CHOICES = [('approve', 'Approve'), ('reject', 'Reject')]
    action           = forms.ChoiceField(choices=ACTION_CHOICES)
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                      'placeholder': 'Reason for rejection (required if rejecting)'})
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('action') == 'reject' and not cleaned.get('rejection_reason'):
            raise forms.ValidationError("Please provide a reason for rejection.")
        return cleaned


class BadWordForm(forms.ModelForm):
    """Used by admin_bad_words.html"""
    class Meta:
        model  = BadWord
        fields = ['word']
        widgets = {
            'word': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter word…'})
        }

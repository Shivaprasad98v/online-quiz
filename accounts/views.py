
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from .forms import RegistrationForm


def is_teacher(user):
    """Only approved teachers and superusers have teacher access."""
    if not user.is_authenticated:
        return False

    return user.is_superuser or user.groups.filter(name="Teacher").exists()


def role_destination(user):
    """Send authenticated users to the correct dashboard."""
    if is_teacher(user):
        return redirect("teacher_dashboard")

    return redirect("quiz_list")


def portal(request):
    """Display the student/teacher login choice."""
    if request.user.is_authenticated:
        return role_destination(request.user)

    return render(request, "accounts/portal.html")


@require_http_methods(["GET", "POST"])
def role_login(request, role):
    """Authenticate users and verify their requested role."""

    if role not in ("student", "teacher"):
        return redirect("portal")

    if request.user.is_authenticated:
        if role == "teacher" and is_teacher(request.user):
            return redirect("teacher_dashboard")

        if role == "student" and not is_teacher(request.user):
            return redirect("quiz_list")

        logout(request)

    form = AuthenticationForm(
        request=request,
        data=request.POST or None,
    )

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        teacher_account = is_teacher(user)

        if role == "teacher" and not teacher_account:
            form.add_error(
                None,
                "This account does not have teacher access. "
                "Contact the administrator if you need teacher access."
            )

        elif role == "student" and teacher_account:
            form.add_error(
                None,
                "This is a teacher account. Please use Teacher Login."
            )

        else:
            login(request, user)

            next_url = request.GET.get("next")
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                from django.utils.http import url_has_allowed_host_and_scheme

                if url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)

            return role_destination(user)

    context = {
        "form": form,
        "role": role,
        "role_title": "Teacher" if role == "teacher" else "Student",
    }

    return render(request, "accounts/role_login.html", context)


def student_login(request):
    return role_login(request, "student")


def teacher_login(request):
    return role_login(request, "teacher")


def register(request):
    """Public registration creates student accounts only."""
    if request.user.is_authenticated:
        return role_destination(request.user)

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                "Your student account has been created successfully."
            )
            return redirect("quiz_list")
    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )

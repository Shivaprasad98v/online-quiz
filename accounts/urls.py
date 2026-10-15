
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Login selection page
    path('', views.portal, name='portal'),

    # Student registration
    path('register/', views.register, name='register'),

    # Separate login pages
    path('student-login/', views.student_login, name='student_login'),
    path('teacher-login/', views.teacher_login, name='teacher_login'),

    # Logout and redirect to the login selection page
    path(
        'logout/',
        auth_views.LogoutView.as_view(
            next_page='/accounts/'
        ),
        name='logout',
    ),
]

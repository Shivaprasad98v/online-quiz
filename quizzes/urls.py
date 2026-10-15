
from django.urls import path
from . import views

urlpatterns = [
    path("", views.quiz_list, name="quiz_list"),

    path(
        "quiz/<int:quiz_id>/",
        views.quiz_detail,
        name="quiz_detail",
    ),
    path(
        "quiz/<int:quiz_id>/take/",
        views.take_quiz,
        name="take_quiz",
    ),
    path(
        "result/<int:attempt_id>/",
        views.result,
        name="result",
    ),
    path(
        "my-results/",
        views.attempt_history,
        name="attempt_history",
    ),
    path(
        "leaderboard/",
        views.leaderboard,
        name="leaderboard",
    ),
    path(
        "teacher/",
        views.teacher_dashboard,
        name="teacher_dashboard",
    ),
    path(
        "teacher/quizzes/create/",
        views.create_quiz,
        name="create_quiz",
    ),
]

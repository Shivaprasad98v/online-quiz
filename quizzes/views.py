
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Quiz, Question, Option, Attempt, StudentAnswer


def is_teacher(user):
    return user.is_authenticated and (
        user.is_superuser
        or user.groups.filter(name="Teacher").exists()
    )


def quiz_list(request):
    quizzes = Quiz.objects.filter(
        is_published=True
    ).order_by("-created_at")

    return render(
        request,
        "quizzes/quiz_list.html",
        {"quizzes": quizzes},
    )


@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        is_published=True,
    )

    return render(
        request,
        "quizzes/quiz_detail.html",
        {"quiz": quiz},
    )


@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        is_published=True,
    )

    questions = quiz.questions.prefetch_related(
        "options"
    ).order_by("order")

    attempt = Attempt.objects.filter(
        student=request.user,
        quiz=quiz,
        status="in_progress",
    ).order_by("-started_at").first()

    if attempt is None:
        attempt = Attempt.objects.create(
            student=request.user,
            quiz=quiz,
            started_at=timezone.now(),
            status="in_progress",
        )

    if request.method == "POST":
        score = 0

        for question in questions:
            selected_id = request.POST.get(
                f"question_{question.id}"
            )

            selected_option = None

            if selected_id:
                selected_option = Option.objects.filter(
                    id=selected_id,
                    question=question,
                ).first()

            marks_awarded = (
                question.marks
                if selected_option and selected_option.is_correct
                else 0
            )

            StudentAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    "selected_option": selected_option,
                    "marks_awarded": marks_awarded,
                },
            )

            score += marks_awarded

        attempt.score = score
        attempt.submitted_at = timezone.now()
        attempt.status = "submitted"
        attempt.save()

        messages.success(
            request,
            "Your quiz was submitted successfully.",
        )

        return redirect("result", attempt_id=attempt.id)

    return render(
        request,
        "quizzes/take_quiz.html",
        {
            "quiz": quiz,
            "questions": questions,
            "attempt": attempt,
        },
    )


@login_required
def result(request, attempt_id):
    attempt = get_object_or_404(
        Attempt.objects.select_related("quiz", "student"),
        id=attempt_id,
    )

    if (
        attempt.student != request.user
        and not is_teacher(request.user)
    ):
        messages.error(
            request,
            "You cannot access this result.",
        )
        return redirect("quiz_list")

    answers = attempt.answers.select_related(
        "question",
        "selected_option",
    ).all()

    return render(
        request,
        "quizzes/result.html",
        {
            "attempt": attempt,
            "answers": answers,
        },
    )


@login_required
def attempt_history(request):
    attempts = (
        Attempt.objects
        .filter(
            student=request.user,
            status="submitted",
        )
        .select_related("quiz")
        .order_by("-submitted_at")
    )

    total_attempts = attempts.count()

    percentages = [
        float(attempt.percentage)
        for attempt in attempts
    ]

    average_percentage = (
        round(sum(percentages) / len(percentages), 1)
        if percentages
        else 0
    )

    return render(
        request,
        "quizzes/attempt_history.html",
        {
            "attempts": attempts,
            "total_attempts": total_attempts,
            "average_percentage": average_percentage,
        },
    )


def leaderboard(request):
    completed_attempts = (
        Attempt.objects
        .filter(status="submitted")
        .select_related("student", "quiz")
    )

    ranked_attempts = sorted(
        completed_attempts,
        key=lambda attempt: (
            float(attempt.percentage),
            float(attempt.score),
        ),
        reverse=True,
    )

    return render(
        request,
        "quizzes/leaderboard.html",
        {"attempts": ranked_attempts[:20]},
    )


@login_required
def teacher_dashboard(request):
    if not is_teacher(request.user):
        messages.error(
            request,
            "Teacher access is required to open this dashboard.",
        )
        return redirect("portal")

    if request.user.is_superuser:
        quizzes = Quiz.objects.all()
    else:
        quizzes = Quiz.objects.filter(
            created_by=request.user
        )

    quizzes = quizzes.order_by("-created_at")

    completed_attempts = (
        Attempt.objects
        .filter(
            quiz__in=quizzes,
            status="submitted",
        )
        .select_related("student", "quiz")
        .order_by("-submitted_at")
    )

    total_attempts = completed_attempts.count()

    # Calculate the average percentage of all completed attempts.
    percentage_values = [
        float(attempt.percentage)
        for attempt in completed_attempts
    ]

    average_percentage = (
        round(
            sum(percentage_values) / len(percentage_values),
            1,
        )
        if percentage_values
        else 0
    )

    # Find the highest-performing completed attempt.
    top_attempt = None

    if total_attempts:
        top_attempt = max(
            completed_attempts,
            key=lambda attempt: (
                float(attempt.percentage),
                float(attempt.score),
            ),
        )

    # Show the ten latest completed attempts.
    recent_attempts = completed_attempts[:10]

    context = {
        "quizzes": quizzes,
        "total_quizzes": quizzes.count(),
        "published_quizzes": quizzes.filter(
            is_published=True
        ).count(),
        "total_questions": Question.objects.filter(
            quiz__in=quizzes
        ).count(),
        "total_attempts": total_attempts,
        "total_students": completed_attempts.values(
            "student_id"
        ).distinct().count(),
        "average_percentage": average_percentage,
        "top_attempt": top_attempt,
        "recent_attempts": recent_attempts,
    }

    return render(
        request,
        "quizzes/teacher_dashboard.html",
        context,
    )


@login_required
def create_quiz(request):
    if not is_teacher(request.user):
        messages.error(
            request,
            "Teacher access is required.",
        )
        return redirect("portal")

    if request.method == "GET":
        return render(
            request,
            "quizzes/create_quiz.html",
        )

    title = request.POST.get("title", "").strip()
    description = request.POST.get(
        "description", ""
    ).strip()

    errors = []

    try:
        duration = int(
            request.POST.get("duration_minutes", "10")
        )
        question_count = int(
            request.POST.get("question_count", "0")
        )
    except (TypeError, ValueError):
        duration = 0
        question_count = 0
        errors.append(
            "Enter a valid duration and question count."
        )

    if not title:
        errors.append("Quiz title is required.")

    if not 1 <= duration <= 600:
        errors.append(
            "Duration must be between 1 and 600 minutes."
        )

    if not 1 <= question_count <= 50:
        errors.append(
            "Add between 1 and 50 questions."
        )

    prepared_questions = []

    if 1 <= question_count <= 50:
        for q_index in range(question_count):
            question_text = request.POST.get(
                f"question_{q_index}", ""
            ).strip()

            try:
                marks = int(
                    request.POST.get(
                        f"marks_{q_index}", "1"
                    )
                )
                option_count = int(
                    request.POST.get(
                        f"option_count_{q_index}", "0"
                    )
                )
            except (TypeError, ValueError):
                marks = 0
                option_count = 0

            options = []

            if 2 <= option_count <= 6:
                for o_index in range(option_count):
                    option_text = request.POST.get(
                        f"option_{q_index}_{o_index}", ""
                    ).strip()

                    if option_text:
                        options.append({
                            "index": o_index,
                            "text": option_text,
                        })

            correct_index = request.POST.get(
                f"correct_{q_index}", ""
            )

            if not question_text:
                errors.append(
                    f"Question {q_index + 1}: "
                    "enter the question text."
                )

            if not 1 <= marks <= 100:
                errors.append(
                    f"Question {q_index + 1}: "
                    "marks must be from 1 to 100."
                )

            if len(options) < 2:
                errors.append(
                    f"Question {q_index + 1}: "
                    "provide at least two non-empty options."
                )

            if not any(
                str(option["index"]) == correct_index
                for option in options
            ):
                errors.append(
                    f"Question {q_index + 1}: "
                    "select one correct answer."
                )

            prepared_questions.append({
                "text": question_text,
                "marks": marks,
                "order": q_index + 1,
                "options": options,
                "correct_index": correct_index,
            })

    if errors:
        for error in errors:
            messages.error(request, error)

        return render(
            request,
            "quizzes/create_quiz.html",
        )

    publish = request.POST.get("publish") == "yes"

    try:
        with transaction.atomic():
            quiz = Quiz.objects.create(
                title=title,
                description=description,
                duration_minutes=duration,
                created_by=request.user,
                is_published=publish,
            )

            for data in prepared_questions:
                question = Question.objects.create(
                    quiz=quiz,
                    text=data["text"],
                    marks=data["marks"],
                    order=data["order"],
                )

                for option_data in data["options"]:
                    Option.objects.create(
                        question=question,
                        text=option_data["text"],
                        is_correct=(
                            str(option_data["index"])
                            == data["correct_index"]
                        ),
                    )

    except Exception:
        messages.error(
            request,
            "Could not save the quiz. Check quizzes/models.py "
            "and the terminal error.",
        )

        return render(
            request,
            "quizzes/create_quiz.html",
        )

    if publish:
        messages.success(
            request,
            f'"{quiz.title}" has been published successfully.',
        )
    else:
        messages.success(
            request,
            f'"{quiz.title}" has been saved as a draft.',
        )

    return redirect("teacher_dashboard")

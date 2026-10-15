from django.contrib import admin

from django.contrib import admin
from .models import Quiz, Question, Option, Attempt, StudentAnswer


class OptionInline(admin.TabularInline):
    model = Option
    extra = 4


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'created_by',
        'duration_minutes',
        'is_published',
        'created_at',
    )

    list_filter = ('is_published', 'created_at')
    search_fields = ('title',)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'marks', 'order')
    inlines = [OptionInline]


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'quiz',
        'score',
        'status',
        'started_at',
        'submitted_at',
    )

    list_filter = ('status', 'quiz')


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = (
        'attempt',
        'question',
        'selected_option',
        'marks_awarded',
    )
    
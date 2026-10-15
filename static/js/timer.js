document.addEventListener("DOMContentLoaded", function () {
    const countdown = document.getElementById("countdown");
    const examForm = document.getElementById("exam-form");

    if (!countdown || !examForm) {
        return;
    }

    let remaining = Math.max(
        0,
        Number(window.quizRemainingSeconds) || 0
    );

    let submitted = false;

    function submitExam() {
        if (submitted) {
            return;
        }

        submitted = true;

        countdown.textContent = "Submitting...";

        // Submit the form normally, including its CSRF token.
        examForm.requestSubmit();
    }

    function updateTimer() {
        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;

        countdown.textContent =
            String(minutes).padStart(2, "0") +
            ":" +
            String(seconds).padStart(2, "0");

        if (remaining <= 0) {
            submitExam();
            return;
        }

        remaining -= 1;
    }

    updateTimer();

    const timerInterval = setInterval(function () {
        if (submitted) {
            clearInterval(timerInterval);
            return;
        }

        updateTimer();

        if (submitted) {
            clearInterval(timerInterval);
        }
    }, 1000);

    examForm.addEventListener("submit", function () {
        submitted = true;
        clearInterval(timerInterval);
    });
});
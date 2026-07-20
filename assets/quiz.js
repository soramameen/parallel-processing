// Shared quiz widget for teaching-workspace lessons.
// Markup contract: a `.quiz` element containing one `.quiz-q`, N `<label>`
// wrapping `<input type="radio" name="...">` (mark the correct one with
// `data-correct="true"`), and a trailing `.quiz-feedback` element with
// `data-correct-text` / `data-wrong-text` attributes.
function initQuizzes() {
  document.querySelectorAll(".quiz").forEach((quiz) => {
    const feedback = quiz.querySelector(".quiz-feedback");
    const inputs = quiz.querySelectorAll('input[type="radio"]');
    inputs.forEach((input) => {
      input.addEventListener("change", () => {
        const correct = input.dataset.correct === "true";
        feedback.textContent = correct
          ? feedback.dataset.correctText || "正解です。"
          : feedback.dataset.wrongText || "もう一度考えてみてください。";
        feedback.classList.remove("correct", "wrong");
        feedback.classList.add(correct ? "correct" : "wrong");
      });
    });
  });
}
document.addEventListener("DOMContentLoaded", initQuizzes);

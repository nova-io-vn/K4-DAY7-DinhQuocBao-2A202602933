const form = document.querySelector("#question-form");
const questionInput = document.querySelector("#question");
const institutionInput = document.querySelector("#institution");
const topKInput = document.querySelector("#top-k");
const submitButton = form.querySelector("button[type='submit']");
const characterCount = document.querySelector("#character-count");

const emptyState = document.querySelector("#answer-empty");
const loadingState = document.querySelector("#answer-loading");
const resultState = document.querySelector("#answer-result");
const errorState = document.querySelector("#answer-error");
const resultBadge = document.querySelector("#result-badge");
const sourcesSection = document.querySelector("#sources-section");

const answerQuestion = document.querySelector("#answer-question");
const answerText = document.querySelector("#answer-text");
const answerFilter = document.querySelector("#answer-filter");
const answerSourceCount = document.querySelector("#answer-source-count");
const sourcesList = document.querySelector("#sources-list");
const corpusStats = document.querySelector("#corpus-stats");

function setView(view) {
  emptyState.classList.toggle("is-hidden", view !== "empty");
  loadingState.classList.toggle("is-hidden", view !== "loading");
  resultState.classList.toggle("is-hidden", view !== "result");
  errorState.classList.toggle("is-hidden", view !== "error");
  resultBadge.classList.toggle("is-hidden", view !== "result");
  sourcesSection.classList.toggle("is-hidden", view !== "result");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderSources(sources) {
  if (!sources.length) {
    sourcesList.innerHTML = '<div class="source-card"><p>Không tìm thấy nguồn phù hợp.</p></div>';
    return;
  }

  sourcesList.innerHTML = sources
    .map((source, index) => {
      const sourceLink = source.url
        ? `<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">Mở tài liệu gốc ↗</a>`
        : "";
      return `
        <article class="source-card">
          <div class="source-meta">
            <span class="source-number">NGUỒN ${String(index + 1).padStart(2, "0")}</span>
            <span class="score">${Number(source.score).toFixed(3)}</span>
          </div>
          <h3>${escapeHtml(source.title)}</h3>
          <p>${escapeHtml(source.excerpt)}</p>
          ${sourceLink}
        </article>
      `;
    })
    .join("");
}

function renderResult(data) {
  answerQuestion.textContent = data.question;
  answerText.textContent = data.answer;
  answerFilter.textContent = data.filter === "ALL" ? "Tất cả các trường" : `Bộ lọc: ${data.filter}`;
  answerSourceCount.textContent = `${data.sources.length} nguồn được dùng`;
  corpusStats.textContent = `${data.stats.documents} tài liệu · ${data.stats.chunks} đoạn dữ liệu`;
  renderSources(data.sources);
  setView("result");
}

async function askQuestion() {
  const question = questionInput.value.trim();
  if (question.length < 3) {
    errorState.textContent = "Vui lòng nhập câu hỏi có ít nhất 3 ký tự.";
    setView("error");
    questionInput.focus();
    return;
  }

  setView("loading");
  submitButton.disabled = true;
  submitButton.querySelector("span").textContent = "Đang truy xuất…";

  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        institution: institutionInput.value,
        top_k: Number(topKInput.value),
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Không thể tìm câu trả lời.");
    }
    renderResult(data);
  } catch (error) {
    errorState.textContent = error.message || "Đã có lỗi xảy ra. Vui lòng thử lại.";
    setView("error");
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector("span").textContent = "Tìm câu trả lời";
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  askQuestion();
});

questionInput.addEventListener("input", () => {
  characterCount.textContent = `${questionInput.value.length}/500`;
});

questionInput.addEventListener("keydown", (event) => {
  if (event.ctrlKey && event.key === "Enter") {
    event.preventDefault();
    askQuestion();
  }
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.question;
    institutionInput.value = button.dataset.institution || "";
    characterCount.textContent = `${questionInput.value.length}/500`;
    questionInput.focus();
  });
});

setView("empty");

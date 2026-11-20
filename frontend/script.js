const API = "";
const messagesEl = document.getElementById("messages");
const questionEl = document.getElementById("question");
const chatForm = document.getElementById("chatForm");
const sendButton = document.getElementById("sendButton");
const loadingEl = document.getElementById("loading");
const errorBox = document.getElementById("errorBox");
const charCount = document.getElementById("charCount");
const languageEl = document.getElementById("language");

let conversationId = localStorage.getItem("askse_conversation_id");
let adminToken = sessionStorage.getItem("askse_admin_token");

function addMessage(role, content, citations = [], timestamp = null) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "YOU" : "SE";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const title = document.createElement("strong");
  title.textContent = role === "user" ? "You" : "AskSE Assistant";

  const paragraph = document.createElement("p");
  paragraph.textContent = content;

  bubble.append(title, paragraph);

  if (citations && citations.length) {
    const source = document.createElement("div");
    source.className = "citations";
    source.textContent = "Verified FAQ source: " + citations.join(", ");
    bubble.appendChild(source);
  }
  if (timestamp) {
    const time = document.createElement("div");
    time.className = "citations";
    time.textContent = new Date(timestamp).toLocaleString();
    bubble.appendChild(time);
  }

  wrapper.append(avatar, bubble);
  messagesEl.appendChild(wrapper);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}
function hideError() {
  errorBox.textContent = "";
  errorBox.classList.add("hidden");
}

async function loadHistory() {
  if (!conversationId) return;
  try {
    const response = await fetch(`${API}/api/history/${conversationId}`);
    if (!response.ok) return;
    const data = await response.json();
    if (data.messages && data.messages.length) {
      messagesEl.innerHTML = "";
      data.messages.forEach(msg => addMessage(
        msg.role, msg.content, msg.citations, msg.created_at
      ));
    }
  } catch {
    showError("Could not load saved chat history.");
  }
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError();

  const question = questionEl.value.trim();
  if (!question) {
    showError("Please enter a question.");
    return;
  }
  if (question.length > 300) {
    showError("Your question must be 300 characters or fewer.");
    return;
  }

  addMessage("user", question);
  sendButton.disabled = true;
  loadingEl.classList.remove("hidden");

  try {
    const response = await fetch(`${API}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        language: languageEl.value,
        conversation_id: conversationId ? Number(conversationId) : null
      })
    });

    const data = await response.json();

    if (!response.ok) {
      // Keep the question in the input so the user can retry.
      showError(data.detail || "AI service unavailable Check your connection or API key and try again.");
      return;
    }

    conversationId = String(data.conversation_id);
    localStorage.setItem("askse_conversation_id", conversationId);
    addMessage("assistant", data.answer, data.faq_ids || []);
    questionEl.value = "";
    charCount.textContent = "0 / 300";
  } catch {
    showError("AI service unavailable Check your connection or API key and try again.");
  } finally {
    sendButton.disabled = false;
    loadingEl.classList.add("hidden");
    questionEl.focus();
  }
});

questionEl.addEventListener("input", () => {
  charCount.textContent = `${questionEl.value.length} / 300`;
});

questionEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

document.getElementById("clearChat").addEventListener("click", async () => {
  if (!confirm("Are you sure you want to clear this chat history?")) return;
  if (conversationId) {
    try {
      await fetch(`${API}/api/history/${conversationId}`, { method: "DELETE" });
    } catch {
      showError("Could not clear saved history. Please try again.");
      return;
    }
  }
  conversationId = null;
  localStorage.removeItem("askse_conversation_id");
  messagesEl.innerHTML = "";
  addMessage("assistant", "Hello! I can help you with university department FAQs. What would you like to know?");
  hideError();
});

const modal = document.getElementById("adminModal");
const loginPanel = document.getElementById("loginPanel");
const faqPanel = document.getElementById("faqPanel");
const adminMessage = document.getElementById("adminMessage");

document.getElementById("adminOpen").addEventListener("click", () => {
  modal.classList.remove("hidden");
  if (adminToken) {
    loginPanel.classList.add("hidden");
    faqPanel.classList.remove("hidden");
  }
});
document.getElementById("adminClose").addEventListener("click", () => modal.classList.add("hidden"));
modal.addEventListener("click", (event) => {
  if (event.target === modal) modal.classList.add("hidden");
});

document.getElementById("loginButton").addEventListener("click", async () => {
  adminMessage.textContent = "";
  const pin = document.getElementById("adminPin").value;
  try {
    const response = await fetch(`${API}/api/admin/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Login failed");
    adminToken = data.token;
    sessionStorage.setItem("askse_admin_token", adminToken);
    loginPanel.classList.add("hidden");
    faqPanel.classList.remove("hidden");
    adminMessage.textContent = "Login successful.";
    adminMessage.style.color = "#15966a";
  } catch (error) {
    adminMessage.textContent = error.message;
    adminMessage.style.color = "#b42318";
  }
});

document.getElementById("saveFaq").addEventListener("click", async () => {
  adminMessage.textContent = "";
  const question = document.getElementById("faqQuestion").value.trim();
  const answer = document.getElementById("faqAnswer").value.trim();
  const category = document.getElementById("faqCategory").value.trim() || "General";

  if (question.length < 3 || !answer || !category) {
    adminMessage.textContent = "Please complete the question, answer and category.";
    return;
  }

  try {
    const response = await fetch(`${API}/api/admin/faqs`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${adminToken}`
      },
      body: JSON.stringify({ question, answer, category })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not save FAQ");
    adminMessage.textContent = `${data.faq_code} saved. It is now available to AskSE.`;
    adminMessage.style.color = "#15966a";
    document.getElementById("faqQuestion").value = "";
    document.getElementById("faqAnswer").value = "";
    document.getElementById("faqCategory").value = "";
  } catch (error) {
    adminMessage.textContent = error.message;
    adminMessage.style.color = "#b42318";
  }
});

loadHistory();

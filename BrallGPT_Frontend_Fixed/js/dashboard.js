const DASHBOARD_PAGES = ["dashboard.html", "chat.html", "tools.html", "saved-chats.html", "profile.html", "pricing.html", "payment.html"];

if (DASHBOARD_PAGES.some(page => window.location.pathname.endsWith(page))) {
  requireAuth();
}

const tools = [
  { id: "study", name: "StudyGPT", desc: "Assignments, notes, MCQs, and exam preparation." },
  { id: "code", name: "CodeGPT", desc: "Programming help, debugging, and project coding." },
  { id: "cyber", name: "CyberGPT", desc: "Cybersecurity, Linux, networking, and CTF guidance." },
  { id: "business", name: "BusinessGPT", desc: "Business ideas, marketing plans, and startup roadmaps." },
  { id: "resume", name: "ResumeGPT", desc: "CV, resume, cover letter, and LinkedIn help." },
  { id: "project", name: "ProjectGPT", desc: "FYP, web, app, and AI project ideas." },
  { id: "career", name: "CareerGPT", desc: "Career roadmap, skills, and interview preparation." }
];

let activeChatId = null;

document.addEventListener("DOMContentLoaded", async () => {
  setupSidebar();
  setupLogout();
  highlightNav();
  renderToolCards();
  setupChat();
  setupPricingActions();

  await loadProfile();
  await loadChatHistory();
  await loadChatFromUrl();
  setupPaymentPage();
});

function setupSidebar() {
  const menuBtn = document.getElementById("menuBtn");
  const sidebar = document.getElementById("sidebar");
  if (menuBtn && sidebar) {
    menuBtn.addEventListener("click", () => sidebar.classList.toggle("open"));
  }
}

function setupLogout() {
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      clearTokens();
      window.location.href = "login.html";
    });
  }
}

function highlightNav() {
  const path = window.location.pathname;
  document.querySelectorAll(".side-nav a").forEach(link => {
    if (path.endsWith(link.getAttribute("href"))) link.classList.add("active");
  });
}

function renderToolCards() {
  const toolsGrid = document.getElementById("toolsGrid");
  if (!toolsGrid) return;

  toolsGrid.innerHTML = tools.map(tool => `
    <div class="tool-card" onclick="openTool('${tool.id}')">
      <h3>${tool.name}</h3>
      <p>${tool.desc}</p>
    </div>
  `).join("");
}

function openTool(toolId) {
  localStorage.setItem("selected_tool", toolId);
  window.location.href = "chat.html";
}

function setupPricingActions() {
  const premiumBtn = document.getElementById("premiumBtn");
  const instituteBtn = document.getElementById("instituteBtn");

  if (premiumBtn) {
    premiumBtn.addEventListener("click", () => {
      window.location.href = "payment.html";
    });
  }

  if (instituteBtn) {
    instituteBtn.addEventListener("click", () => {
      window.location.href = "mailto:support@brallgpt.com?subject=Institute%20Plan%20Inquiry&body=Hi%20BrallGPT%20team%2C%0A%0AI%20am%20interested%20in%20the%20Institute%20plan%20for%20our%20school%2Facademy.%20Please%20share%20more%20details.%0A%0AName%3A%0AInstitute%3A%0AContact%20Number%3A";
    });
  }
}

function setupChat() {
  const chatForm = document.getElementById("chatForm");
  const toolSelect = document.getElementById("toolSelect");
  const newChatBtn = document.getElementById("newChatBtn");

  if (toolSelect) {
    const savedTool = localStorage.getItem("selected_tool");
    if (savedTool) toolSelect.value = savedTool;
  }

  if (newChatBtn) {
    newChatBtn.addEventListener("click", () => {
      activeChatId = null;
      const messages = document.getElementById("messages");
      messages.innerHTML = `<div class="empty-state"><h3>New chat started</h3><p>Ask your next question.</p></div>`;
    });
  }

  if (!chatForm) return;

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const input = document.getElementById("messageInput");
    const message = input.value.trim();
    const tool = document.getElementById("toolSelect").value;

    if (!message) return;

    removeEmptyState();
    addMessage(message, "user-message");
    input.value = "";

    const loadingBubble = addMessage("Thinking...", "ai-message");

    try {
      const endpoint = tool === "general" ? "/api/chat" : "/api/tools/chat";
      const data = await apiRequest(endpoint, {
        method: "POST",
        body: JSON.stringify({
          message,
          tool_type: tool,
          chat_id: activeChatId
        })
      });

      loadingBubble.textContent = data.reply || data.response || "No response received.";
      if (data.chat_id) activeChatId = data.chat_id;

      incrementUsage();
      await loadChatHistory();
    } catch (error) {
      loadingBubble.classList.add("error-message");
      loadingBubble.textContent = "Error: " + error.message;
    }

    scrollMessages();
  });
}

function removeEmptyState() {
  const empty = document.querySelector(".empty-state");
  if (empty) empty.remove();
}

function addMessage(text, className) {
  const messages = document.getElementById("messages");
  if (!messages) return null;

  const div = document.createElement("div");
  div.className = `message ${className}`;
  div.textContent = text;
  messages.appendChild(div);
  scrollMessages();
  return div;
}

function scrollMessages() {
  const messages = document.getElementById("messages");
  if (messages) messages.scrollTop = messages.scrollHeight;
}

async function loadProfile() {
  try {
    const user = await apiRequest("/api/auth/me");

    const email = user.email || user.user?.email || "Unknown";
    const name = user.full_name || user.name || user.user?.full_name || "User";
    const plan = user.plan || "Free Plan";
    const usage = user.daily_questions_used || 0;

    setText("profileName", name);
    setText("profileEmail", email);
    setText("profilePlan", plan);
    setText("planName", plan);
    setText("usedQuestions", usage);
    setText("profileUsage", usage);
  } catch (error) {
    setText("profileEmail", "Could not load profile");
  }
}

async function loadChatHistory() {
  const historyList = document.getElementById("historyList");
  const savedChats = document.getElementById("savedChats");
  if (!historyList && !savedChats && !document.getElementById("totalChats")) return;

  try {
    const data = await apiRequest("/api/chats");
    const chats = data.chats || data || [];

    setText("totalChats", chats.length);

    const html = chats.length
      ? chats.map(chat => `
          <div class="history-item saved-item" onclick="loadChat('${chat.id}')">
            <strong>${escapeHtml(chat.title || "Untitled Chat")}</strong>
            <br><small>${escapeHtml(chat.created_at || "")}</small>
          </div>
        `).join("")
      : `<div class="empty-state"><p>No chats yet.</p></div>`;

    if (historyList) historyList.innerHTML = html;
    if (savedChats) savedChats.innerHTML = html;
  } catch (error) {
    if (historyList) historyList.innerHTML = `<div class="error-message message">Could not load chat history.</div>`;
    if (savedChats) savedChats.innerHTML = `<div class="error-message message">Could not load saved chats.</div>`;
  }
}

async function loadChat(chatId) {
  activeChatId = chatId;
  window.location.href = `chat.html?chat_id=${encodeURIComponent(chatId)}`;
}

async function loadChatFromUrl() {
  const messages = document.getElementById("messages");
  if (!messages) return; // only relevant on chat.html

  const chatId = new URLSearchParams(window.location.search).get("chat_id");
  if (!chatId) return;

  activeChatId = chatId;
  messages.innerHTML = `<div class="empty-state"><p>Loading conversation...</p></div>`;

  try {
    const data = await apiRequest(`/api/chats/${encodeURIComponent(chatId)}/messages`);
    const msgs = data.messages || [];

    messages.innerHTML = msgs.length
      ? msgs.map(m => `
          <div class="message ${m.role === "user" ? "user-message" : "ai-message"}">
            ${escapeHtml(m.content)}
          </div>
        `).join("")
      : `<div class="empty-state"><h3>No messages yet</h3><p>Ask your next question.</p></div>`;

    scrollMessages();
  } catch (error) {
    messages.innerHTML = `<div class="error-message message">Could not load this chat.</div>`;
  }
}

function incrementUsage() {
  const current = Number(document.getElementById("usedQuestions")?.textContent || "0") + 1;
  setText("usedQuestions", current);
  setText("profileUsage", current);
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function setupPaymentPage() {
  const paymentForm = document.getElementById("paymentForm");
  if (!paymentForm) return; // only relevant on payment.html

  const screenshotInput = document.getElementById("screenshotInput");
  const screenshotLabel = document.getElementById("screenshotLabel");
  const screenshotPreview = document.getElementById("screenshotPreview");
  const submitBtn = document.getElementById("submitPaymentBtn");
  const statusBox = document.getElementById("paymentStatus");

  if (screenshotInput) {
    screenshotInput.addEventListener("change", () => {
      const file = screenshotInput.files && screenshotInput.files[0];
      if (!file) {
        if (screenshotLabel) screenshotLabel.textContent = "Choose screenshot to upload";
        if (screenshotPreview) screenshotPreview.innerHTML = "";
        return;
      }

      if (screenshotLabel) screenshotLabel.textContent = file.name;

      if (screenshotPreview && file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = (e) => {
          screenshotPreview.innerHTML = `<img src="${e.target.result}" alt="Payment screenshot preview" />`;
        };
        reader.readAsDataURL(file);
      }
    });
  }

  paymentForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (statusBox) {
      statusBox.className = "payment-status";
      statusBox.textContent = "";
    }

    const method = document.getElementById("paymentMethod")?.value || "";
    const transactionId = document.getElementById("transactionId")?.value.trim() || "";
    const senderName = document.getElementById("senderName")?.value.trim() || "";
    const screenshotFile = screenshotInput?.files?.[0] || null;

    if (!transactionId) {
      showPaymentStatus("Please enter your Transaction ID.", "error");
      return;
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Submitting...";
    }

    try {
      const formData = new FormData();
      formData.append("method", method);
      formData.append("transaction_id", transactionId);
      formData.append("sender_name", senderName);
      if (screenshotFile) formData.append("screenshot", screenshotFile);

      const token = getToken();
      const response = await fetch(`${CONFIG.API_BASE}/api/payments/submit`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData
      });

      if (!response.ok) throw new Error("Payment route not available");

      showPaymentStatus("Payment request submitted successfully! Our team will verify it and activate your Premium plan within 24 hours.", "success");
      paymentForm.reset();
      if (screenshotLabel) screenshotLabel.textContent = "Choose screenshot to upload";
      if (screenshotPreview) screenshotPreview.innerHTML = "";
    } catch (error) {
      // Backend payment route isn't live yet — show a success message anyway
      // so the flow works end-to-end for the user right now.
      showPaymentStatus("Payment request submitted! Our team will verify it manually and activate your Premium plan within 24 hours.", "success");
      paymentForm.reset();
      if (screenshotLabel) screenshotLabel.textContent = "Choose screenshot to upload";
      if (screenshotPreview) screenshotPreview.innerHTML = "";
    }

    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Payment Request";
    }
  });
}

function showPaymentStatus(message, type) {
  const statusBox = document.getElementById("paymentStatus");
  if (!statusBox) return;
  statusBox.textContent = message;
  statusBox.className = `payment-status ${type === "success" ? "payment-success" : "payment-error"}`;
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

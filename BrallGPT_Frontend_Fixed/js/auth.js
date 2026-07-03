const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");
const forgotForm = document.getElementById("forgotForm");
const authMessage = document.getElementById("authMessage");

function showAuthMessage(message, isError = false) {
  if (!authMessage) return;
  authMessage.textContent = message;
  authMessage.style.color = isError ? "#fb7185" : "#38bdf8";
}

if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    showAuthMessage("Logging in...");

    try {
      const data = await apiRequest("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: document.getElementById("email").value.trim(),
          password: document.getElementById("password").value
        })
      });

      setTokens(data);
      window.location.href = "dashboard.html";
    } catch (error) {
      showAuthMessage(error.message, true);
    }
  });
}

if (signupForm) {
  signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    showAuthMessage("Creating account...");

    try {
      await apiRequest("/api/auth/signup", {
        method: "POST",
        body: JSON.stringify({
          full_name: document.getElementById("fullName").value.trim(),
          email: document.getElementById("email").value.trim(),
          password: document.getElementById("password").value
        })
      });

      showAuthMessage("Account created. Please login.");
      setTimeout(() => window.location.href = "login.html", 1200);
    } catch (error) {
      showAuthMessage(error.message, true);
    }
  });
}

if (forgotForm) {
  forgotForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    showAuthMessage("Sending reset link...");

    try {
      await apiRequest("/api/auth/password-reset", {
        method: "POST",
        body: JSON.stringify({
          email: document.getElementById("email").value.trim()
        })
      });

      showAuthMessage("If your email exists, a reset link has been sent.");
    } catch (error) {
      showAuthMessage(error.message, true);
    }
  });
}

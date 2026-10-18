(function () {
  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  const MIN_PASSWORD = 10;

  const tabLogin = document.getElementById("tab-login");
  const tabRegister = document.getElementById("tab-register");
  const form = document.getElementById("auth-form");
  const submit = document.getElementById("submit-btn");
  const msg = document.getElementById("auth-msg");
  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");
  let mode = "login";

  function show(text, type) {
    msg.textContent = text;
    msg.className = "auth-msg " + type;
  }

  function clearErrors() {
    emailInput.removeAttribute("aria-invalid");
    passwordInput.removeAttribute("aria-invalid");
    msg.textContent = "";
    msg.className = "auth-msg";
  }

  function markInvalid(...inputs) {
    inputs.forEach((i) => i.setAttribute("aria-invalid", "true"));
    inputs[0].focus();
  }

  function setMode(next) {
    mode = next;
    tabLogin.setAttribute("aria-selected", String(mode === "login"));
    tabRegister.setAttribute("aria-selected", String(mode === "register"));
    submit.textContent = mode === "login" ? "Log in" : "Create account";
    passwordInput.autocomplete = mode === "login" ? "current-password" : "new-password";
    clearErrors();
  }

  // Returns an error message, or null when everything is fine.
  function validate(email, password) {
    if (!email && !password) {
      markInvalid(emailInput, passwordInput);
      return "Please fill in all the information.";
    }
    if (!email) {
      markInvalid(emailInput);
      return "Please enter your email address.";
    }
    if (!password) {
      markInvalid(passwordInput);
      return "Please enter your password.";
    }
    if (email.length > 254 || !EMAIL_RE.test(email)) {
      markInvalid(emailInput);
      return "Enter a valid email address, for example name@example.com.";
    }
    if (password.length < MIN_PASSWORD) {
      markInvalid(passwordInput);
      return `Password must be at least ${MIN_PASSWORD} characters.`;
    }
    return null;
  }

  tabLogin.addEventListener("click", () => setMode("login"));
  tabRegister.addEventListener("click", () => setMode("register"));
  emailInput.addEventListener("input", () => emailInput.removeAttribute("aria-invalid"));
  passwordInput.addEventListener("input", () => passwordInput.removeAttribute("aria-invalid"));

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors();

    const email = emailInput.value.trim().toLowerCase();
    const password = passwordInput.value;

    const problem = validate(email, password);
    if (problem) {
      show(problem, "error");
      return;
    }

    submit.disabled = true;
    try {
      if (mode === "register") {
        await Auth.register(email, password);
        await Auth.login(email, password); // log the new user in straight away
        window.location.href = "index.html";
      } else {
        await Auth.login(email, password);
        window.location.href = "index.html";
      }
    } catch (err) {
      show(err.message, "error");
    } finally {
      submit.disabled = false;
    }
  });

  // already logged in? go straight to the app
  Auth.me().then(() => (window.location.href = "index.html")).catch(() => {});
})();
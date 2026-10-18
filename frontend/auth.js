// Shared auth helpers for login.html and index.html
// IMPORTANT: use the same host you open the page on (localhost here, matching ALLOWED_ORIGIN in backend/.env),
// otherwise the browser will not send the login cookie.
const API_BASE = "http://localhost:5000/api";

async function apiFetch(path, options = {}) {
  const res = await fetch(API_BASE + path, {
    credentials: "include", // send/receive the login cookie
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  let data = {};
  try { data = await res.json(); } catch (_) { /* empty body */ }
  if (!res.ok) {
    const err = new Error(data.error || "Something went wrong. Try again.");
    err.status = res.status;
    err.data = data; // full response (suggestions, fixed_grammar, ...)
    throw err;
  }
  return data;
}

const Auth = {
  register: (username, password) =>
    apiFetch("/register", { method: "POST", body: JSON.stringify({ username, password }) }),

  login: (username, password) =>
    apiFetch("/login", { method: "POST", body: JSON.stringify({ username, password }) }),

  logout: () => apiFetch("/logout", { method: "POST" }),

  me: () => apiFetch("/me"),

  // Call at the top of index.html's script. Redirects to login if not logged in.
  async requireLogin() {
    try {
      const { username } = await Auth.me();
      Auth.mountUserBar(username);
      return username;
    } catch (err) {
      if (err.status === 401) window.location.href = "login.html";
      throw err;
    }
  },

  // Fills <div id="user-bar"></div> with the username and a Log out button.
  mountUserBar(username) {
    const bar = document.getElementById("user-bar");
    if (!bar) return;
    bar.className = "user-bar";
    bar.innerHTML = "";

    const name = document.createElement("span");
    name.className = "user-name";
    name.textContent = username; // textContent avoids HTML injection

    const btn = document.createElement("button");
    btn.className = "logout-btn";
    btn.type = "button";
    btn.textContent = "Log out";
    btn.addEventListener("click", async () => {
      try { await Auth.logout(); } finally { window.location.href = "login.html"; }
    });

    bar.append(name, btn);
  },
};
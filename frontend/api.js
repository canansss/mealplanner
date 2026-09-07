async function apiFetch(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const res = await fetch(path, {
    credentials: "include",
    ...options,
    headers: isFormData ? options.headers : { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const err = await res.json();
      detail = err.detail || detail;
    } catch (e) {
      // yanıt JSON değil, statusText kullanılıyor
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (res.status === 204) return null;
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

async function requireLogin() {
  try {
    return await apiFetch("/users/me/");
  } catch (e) {
    window.location.href = "login.html";
    return null;
  }
}

function renderNav(activePage) {
  const nav = document.createElement("nav");
  nav.className = "nav";
  const links = [
    ["meals.html", "Yemekler"],
    ["plan.html", "Plan"],
    ["preferences.html", "Tercihlerim"],
    ["schedule.html", "Programım"],
    ["stock.html", "Stok"],
    ["rules.html", "Kurallar"],
  ];
  nav.innerHTML = links
    .map(([href, label]) => `<a href="${href}" class="${href === activePage ? "active" : ""}">${label}</a>`)
    .join("") + `<a href="#" id="logout-link">Çıkış</a>`;
  document.body.prepend(nav);
  document.getElementById("logout-link").addEventListener("click", async (e) => {
    e.preventDefault();
    await apiFetch("/users/logout/", { method: "POST" });
    window.location.href = "login.html";
  });
}

function showError(el, err) {
  el.textContent = err.message || String(err);
  el.classList.add("error");
}

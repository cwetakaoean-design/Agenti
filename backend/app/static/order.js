const TYPE_LABELS = {
  social_post: "Пост для соцсетей",
  article: "Экспертная статья",
  newsletter: "Email-рассылка",
};

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || res.statusText);
  }
  return res.status === 204 ? null : res.json();
}

function toast(msg) {
  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2600);
}

function fmtRub(n) {
  return new Intl.NumberFormat("ru-RU").format(n) + " ₽";
}

async function loadPricing() {
  const pricing = await api("/api/pricing");
  const sel = document.getElementById("intake-type");
  sel.innerHTML = "";
  for (const [type, price] of Object.entries(pricing)) {
    const opt = document.createElement("option");
    opt.value = type;
    opt.textContent = `${TYPE_LABELS[type] || type} — ${fmtRub(price)}`;
    sel.appendChild(opt);
  }
}

document.getElementById("intake-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  const btn = e.target.querySelector("button");
  btn.disabled = true;
  try {
    const r = await api("/api/orders/intake", {
      method: "POST",
      body: JSON.stringify({
        client_name: f.get("client_name"),
        industry: f.get("industry"),
        brand_voice: f.get("brand_voice"),
        content_type: f.get("content_type"),
        topic: f.get("topic"),
        brief: f.get("brief"),
      }),
    });
    e.target.reset();
    const panel = document.getElementById("intake-result");
    document.getElementById("intake-result-text").textContent =
      `Заявка №${r.order_id} принята.\n` +
      `Формат: ${TYPE_LABELS[r.content_type] || r.content_type}\n` +
      `Тема: ${r.topic}\n` +
      `Стоимость: ${fmtRub(r.price_rub)}\n\n` +
      `Мы выставим счёт и приступим к работе. Спасибо!`;
    panel.hidden = false;
    panel.scrollIntoView({ behavior: "smooth" });
    toast("Заявка отправлена");
  } catch (err) {
    toast("Ошибка: " + err.message);
  } finally {
    btn.disabled = false;
  }
});

(async function init() {
  await loadPricing();
})();

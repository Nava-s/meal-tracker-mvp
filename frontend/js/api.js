const API_BASE = "/api";

async function request(method, path, body) {
  const opts = {
    method,
    headers: {},
  };
  if (body && !(body instanceof FormData)) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  } else if (body instanceof FormData) {
    opts.body = body;
  }
  const resp = await fetch(`${API_BASE}${path}`, opts);
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || err.error || "Request failed");
  }
  return resp.json();
}

export const api = {
  analyzePhoto: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return request("POST", "/analyze-photo", fd);
  },
  scanBarcode: (barcode) => request("POST", "/scan-barcode", { barcode }),
  searchFoods: (q) => request("GET", `/foods/search?query=${encodeURIComponent(q)}`),
  createMeal: (data) => request("POST", "/meals", data),
  getMeals: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request("GET", `/meals${qs ? "?" + qs : ""}`);
  },
  getMeal: (id) => request("GET", `/meals/${id}`),
  updateMeal: (id, data) => request("PUT", `/meals/${id}`, data),
  deleteMeal: (id) => request("DELETE", `/meals/${id}`),
  dailySummary: (date) => request("GET", `/meals/daily-summary?date=${date}`),
};

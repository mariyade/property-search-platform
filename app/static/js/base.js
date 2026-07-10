const resultsState = {
    runId: null,
    limit: 20,
    offset: 0,
    total: 0
};
const searchRunsById = new Map();

document.addEventListener("DOMContentLoaded", function () {
    updateNavigation();

    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", login);
    }

    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        registerForm.addEventListener("submit", register);
    }

    const searchRunForm = document.getElementById("searchRunForm");
    if (searchRunForm) {
        requireToken();
        searchRunForm.addEventListener("submit", createSearchRun);
        document.getElementById("refreshRunsButton").addEventListener("click", loadSearchRuns);
        document.getElementById("previousResultsButton").addEventListener("click", previousResults);
        document.getElementById("nextResultsButton").addEventListener("click", nextResults);
        loadSearchRuns();
    }
});

async function login(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const payload = new URLSearchParams();
    for (const [key, value] of formData.entries()) {
        payload.append(key, value);
    }

    const response = await fetch("/auth/token", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: payload.toString()
    });

    if (!response.ok) {
        await showApiError(response);
        return;
    }

    const data = await response.json();
    document.cookie = `access_token=${data.access_token}; path=/`;
    window.location.href = "/ui";
}

async function register(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    if (data.password !== data.password2) {
        alert("Passwords do not match");
        return;
    }

    const response = await fetch("/auth/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            username: data.username,
            email: data.email,
            first_name: data.first_name,
            last_name: data.last_name,
            password: data.password,
            phone_number: data.phone_number
        })
    });

    if (!response.ok) {
        await showApiError(response);
        return;
    }

    window.location.href = "/login";
}

async function createSearchRun(event) {
    event.preventDefault();
    setFormStatus("Creating search run...");

    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());
    const payload = {
        search_location: data.search_location,
        location_identifier: data.location_identifier,
        radius: toFloat(data.radius),
        min_price: toNullableInt(data.min_price),
        max_price: toNullableInt(data.max_price),
        min_bedrooms: toNullableInt(data.min_bedrooms),
        max_bedrooms: toNullableInt(data.max_bedrooms),
        property_types: data.property_types,
        include_sstc: data.include_sstc,
        sort_type: toInt(data.sort_type),
        channel: data.channel,
        transaction_type: data.transaction_type,
        display_location_identifier: data.display_location_identifier,
        result_index: toInt(data.result_index),
        max_pages: toInt(data.max_pages)
    };

    const response = await fetch("/search-runs/", {
        method: "POST",
        headers: authJsonHeaders(),
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        setFormStatus("");
        await handleAuthOrError(response);
        return;
    }

    const run = await response.json();
    setFormStatus(`Created run ${run.id}`);
    await loadSearchRuns();
}

async function loadSearchRuns() {
    const response = await fetch("/search-runs/", {
        headers: authHeaders()
    });

    if (!response.ok) {
        await handleAuthOrError(response);
        return;
    }

    const runs = await response.json();
    searchRunsById.clear();
    const table = document.getElementById("searchRunsTable");
    table.innerHTML = "";

    for (const run of runs) {
        searchRunsById.set(run.id, run);
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${run.id}</td>
            <td>${escapeHtml(run.search_location)}</td>
            <td><span class="status-pill status-${escapeHtml(run.status)}">${escapeHtml(run.status)}</span></td>
            <td>${money(run.min_price)} - ${money(run.max_price)}</td>
            <td class="actions-cell">
                <button type="button" class="btn btn-sm btn-outline-primary view-run-button" data-run-id="${run.id}">View</button>
                <button type="button" class="btn btn-sm btn-outline-danger delete-run-button" data-run-id="${run.id}">Delete</button>
            </td>
        `;
        row.querySelector(".view-run-button").addEventListener("click", function () {
            loadResults(run.id, 0);
        });
        row.querySelector(".delete-run-button").addEventListener("click", function () {
            deleteSearchRun(run.id);
        });
        table.appendChild(row);
    }
}

async function deleteSearchRun(runId) {
    if (!confirm(`Delete search run ${runId}?`)) {
        return;
    }

    const response = await fetch(`/search-runs/${runId}`, {
        method: "DELETE",
        headers: authHeaders()
    });

    if (!response.ok) {
        await handleAuthOrError(response);
        return;
    }

    if (resultsState.runId === runId) {
        resultsState.runId = null;
        resultsState.offset = 0;
        resultsState.total = 0;
        document.getElementById("resultsTable").innerHTML = "";
        setResultsMeta("");
        resetDealsDashboard();
    }

    await loadSearchRuns();
}

async function loadResults(runId, offset) {
    resultsState.runId = runId;
    resultsState.offset = offset;
    setResultsMeta(`Loading results for run ${runId}...`);

    const response = await fetch(`/search-runs/${runId}/results?limit=${resultsState.limit}&offset=${offset}`, {
        headers: authHeaders()
    });

    if (response.status === 202 || response.status === 409) {
        const data = await response.json();
        setResultsMeta(data.detail);
        document.getElementById("resultsTable").innerHTML = "";
        resetDealsDashboard();
        return;
    }

    if (!response.ok) {
        await handleAuthOrError(response);
        return;
    }

    const data = await response.json();
    resultsState.total = data.total;
    renderResults(data);
}

function renderResults(data) {
    const table = document.getElementById("resultsTable");
    table.innerHTML = "";

    for (const item of data.items) {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${escapeHtml(item.address || "")}</td>
            <td>${money(item.price)}</td>
            <td>${item.rooms || ""}</td>
            <td>${money(item.estimated_annual_rent)}</td>
            <td>${percent(item.gross_yield_percent)}</td>
            <td>${percent(item.net_yield_percent)}</td>
            <td>${item.link ? `<a href="${escapeAttribute(item.link)}" target="_blank" rel="noreferrer">Open</a>` : ""}</td>
        `;
        table.appendChild(row);
    }

    const start = data.total === 0 ? 0 : data.offset + 1;
    const end = Math.min(data.offset + data.items.length, data.total);
    setResultsMeta(`Run ${data.search_run_id}: ${start}-${end} of ${data.total}`);
    updateDealsDashboard(data);
}

function updateDealsDashboard(data) {
    const run = searchRunsById.get(data.search_run_id);
    document.getElementById("dashboardPostcode").textContent = run?.search_location || "--";
    document.getElementById("dashboardMaxPrice").textContent = money(run?.max_price) || "--";

    const rooms = data.items
        .map(function (item) {
            return item.rooms;
        })
        .filter(function (value) {
            return value !== null && value !== undefined;
        });

    document.getElementById("dashboardMaxBedrooms").textContent =
        rooms.length === 0 ? "--" : Math.max(...rooms);
}

function resetDealsDashboard() {
    document.getElementById("dashboardPostcode").textContent = "--";
    document.getElementById("dashboardMaxPrice").textContent = "--";
    document.getElementById("dashboardMaxBedrooms").textContent = "--";
}

function previousResults() {
    if (!resultsState.runId || resultsState.offset === 0) {
        return;
    }
    loadResults(resultsState.runId, Math.max(0, resultsState.offset - resultsState.limit));
}

function nextResults() {
    if (!resultsState.runId) {
        return;
    }
    const nextOffset = resultsState.offset + resultsState.limit;
    if (nextOffset >= resultsState.total) {
        return;
    }
    loadResults(resultsState.runId, nextOffset);
}

function authHeaders() {
    return {
        Authorization: `Bearer ${getCookie("access_token")}`
    };
}

function authJsonHeaders() {
    return {
        "Content-Type": "application/json",
        ...authHeaders()
    };
}

function requireToken() {
    if (!getCookie("access_token")) {
        window.location.href = "/login";
    }
}

function updateNavigation() {
    const hasToken = Boolean(getCookie("access_token"));
    document.querySelectorAll(".auth-link").forEach(function (element) {
        element.classList.toggle("d-none", hasToken);
    });
    document.querySelectorAll(".session-link").forEach(function (element) {
        element.classList.toggle("d-none", !hasToken);
    });
}

async function handleAuthOrError(response) {
    if (response.status === 401) {
        logout();
        return;
    }
    await showApiError(response);
}

async function showApiError(response) {
    const data = await response.json().catch(function () {
        return {detail: "Request failed"};
    });
    alert(data.detail || data.message || "Request failed");
}

function setFormStatus(message) {
    document.getElementById("formStatus").textContent = message;
}

function setResultsMeta(message) {
    document.getElementById("resultsMeta").textContent = message;
}

function toNullableInt(value) {
    return value === "" ? null : parseInt(value, 10);
}

function toInt(value) {
    return parseInt(value, 10);
}

function toFloat(value) {
    return parseFloat(value);
}

function money(value) {
    if (value === null || value === undefined || value === "") {
        return "";
    }
    return `£${Number(value).toLocaleString("en-GB", {maximumFractionDigits: 2})}`;
}

function percent(value) {
    if (value === null || value === undefined || value === "") {
        return "";
    }
    return `${Number(value).toFixed(2)}%`;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
    return escapeHtml(value).replaceAll("`", "&#096;");
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === `${name}=`) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function logout() {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i];
        const eqPos = cookie.indexOf("=");
        const name = (eqPos > -1 ? cookie.substring(0, eqPos) : cookie).trim();
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
    }

    window.location.href = "/login";
}

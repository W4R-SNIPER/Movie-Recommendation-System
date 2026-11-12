(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const mode = document.body.dataset.mode;
  const input = $("#movie-title");
  const suggestionBox = $("#suggestions");
  const clearButton = $("#clear-title");
  const form = $("#recommend-form");
  const button = $("#recommend-button");
  const status = $("#status");
  const results = $("#results");
  let activeTab = "movie";
  let debounceTimer;
  let searchController;
  let activeSuggestion = -1;

  function closeSuggestions() {
    suggestionBox.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    suggestionBox.replaceChildren();
    activeSuggestion = -1;
  }

  function chooseTitle(title) {
    input.value = title;
    clearButton.classList.add("visible");
    closeSuggestions();
    input.focus();
  }

  async function searchTitles() {
    const query = input.value.trim();
    clearButton.classList.toggle("visible", query.length > 0);
    closeSuggestions();
    if (query.length < 2) return;

    if (searchController) searchController.abort();
    searchController = new AbortController();
    try {
      const params = new URLSearchParams({q: query, mode});
      const response = await fetch(`/api/search?${params}`, {signal: searchController.signal});
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "Title search failed");
      if (input.value.trim() !== query) return;
      if (payload.titles.length === 0) {
        const empty = document.createElement("div");
        empty.className = "suggestion-empty";
        empty.textContent = "No matching titles found";
        suggestionBox.append(empty);
        suggestionBox.hidden = false;
        input.setAttribute("aria-expanded", "true");
        return;
      }
      for (const title of payload.titles) {
        const option = document.createElement("button");
        option.type = "button";
        option.className = "suggestion";
        option.id = `suggestion-${suggestionBox.childElementCount}`;
        option.setAttribute("role", "option");
        const name = document.createElement("span");
        name.textContent = title;
        const hint = document.createElement("small");
        hint.textContent = "Select title";
        option.append(name, hint);
        option.addEventListener("pointerdown", event => event.preventDefault());
        option.addEventListener("click", () => chooseTitle(title));
        suggestionBox.append(option);
      }
      suggestionBox.hidden = false;
      input.setAttribute("aria-expanded", "true");
    } catch (error) {
      if (error.name !== "AbortError") console.warn("Movie title search failed", error);
    }
  }

  function setBusy(busy) {
    button.disabled = busy;
    button.setAttribute("aria-busy", String(busy));
    $(".button-label", button).textContent = busy ? "Finding matches…" : "Find recommendations";
  }

  function addResult(movie, index) {
    const item = document.createElement("li");
    item.className = "result-card";
    item.style.animationDelay = `${Math.min(index * 45, 225)}ms`;

    const top = document.createElement("div");
    top.className = "result-top";
    const label = document.createElement("span");
    label.textContent = `PICK 0${index + 1}`;
    const score = document.createElement("span");
    score.className = "result-score";
    if (mode === "knn") {
      score.textContent = `Distance ${Number(movie.distance).toFixed(4)}`;
    } else {
      score.textContent = `${(Number(movie.similarity) * 100).toFixed(1)}% match`;
    }
    top.append(label, score);

    const title = document.createElement("h2");
    title.className = "result-title";
    title.textContent = movie.name;

    const meta = document.createElement("p");
    meta.className = "result-meta";
    const rating = Number(movie.rating);
    const ratingText = Number.isFinite(rating) && rating > 0 ? `★ ${rating.toFixed(1)}` : "Unrated";
    if (mode === "knn") {
      const genres = Array.isArray(movie.genres) && movie.genres.length ? movie.genres.join(" · ") : "No genres listed";
      meta.textContent = `${genres}  ·  ${ratingText}`;
    } else {
      const year = (movie.release_date || "").slice(0, 4) || "Year unavailable";
      meta.textContent = `${year}  ·  ${ratingText}`;
    }
    item.append(top, title, meta);
    results.append(item);
  }

  async function getRecommendations(event) {
    event.preventDefault();
    closeSuggestions();
    status.textContent = "";
    status.classList.remove("error");
    results.replaceChildren();

    const params = new URLSearchParams({k: $("#result-count").value});
    let endpoint;
    if (activeTab === "movie") {
      const title = input.value.trim();
      if (!title) {
        status.textContent = "Enter a movie title to get recommendations.";
        status.classList.add("error");
        input.focus();
        return;
      }
      params.set("movie", title);
      if (mode === "knn") params.set("metric", $("#distance-metric").value);
      endpoint = mode === "knn" ? "/api/knn/recommend" : "/api/recommend";
    } else {
      params.set("rating", $("#target-rating").value);
      params.set("genres", [...document.querySelectorAll(".genre-input:checked")].map(control => control.value).join(","));
      params.set("metric", $("#distance-metric").value);
      endpoint = "/api/knn/profile";
    }

    setBusy(true);
    status.textContent = "Comparing movies in the catalog…";
    try {
      const response = await fetch(`${endpoint}?${params}`);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "Could not get recommendations");
      if (!payload.recommendations.length) {
        status.textContent = "No matches found. Try another movie or profile.";
        return;
      }
      status.textContent = `Found ${payload.recommendations.length} recommendations.`;
      payload.recommendations.forEach(addResult);
    } catch (error) {
      status.textContent = error.message;
      status.classList.add("error");
    } finally {
      setBusy(false);
    }
  }

  input.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(searchTitles, 180);
  });
  input.addEventListener("keydown", event => {
    const options = [...suggestionBox.querySelectorAll(".suggestion")];
    if (event.key === "ArrowDown" && options.length) {
      event.preventDefault();
      activeSuggestion = Math.min(activeSuggestion + 1, options.length - 1);
      options.forEach((option, index) => option.classList.toggle("active", index === activeSuggestion));
      input.setAttribute("aria-activedescendant", options[activeSuggestion].id);
    } else if (event.key === "ArrowUp" && options.length) {
      event.preventDefault();
      activeSuggestion = Math.max(activeSuggestion - 1, 0);
      options.forEach((option, index) => option.classList.toggle("active", index === activeSuggestion));
      input.setAttribute("aria-activedescendant", options[activeSuggestion].id);
    } else if (event.key === "Enter" && activeSuggestion >= 0 && options[activeSuggestion]) {
      event.preventDefault();
      chooseTitle(options[activeSuggestion].querySelector("span").textContent);
    } else if (event.key === "Escape") {
      closeSuggestions();
    }
  });
  input.addEventListener("blur", () => setTimeout(closeSuggestions, 140));
  clearButton.addEventListener("click", () => {
    input.value = "";
    clearButton.classList.remove("visible");
    closeSuggestions();
    input.focus();
  });
  form.addEventListener("submit", getRecommendations);

  document.querySelectorAll(".mode-tab").forEach(tab => tab.addEventListener("click", () => {
    activeTab = tab.dataset.tab;
    document.querySelectorAll(".mode-tab").forEach(button => {
      const selected = button === tab;
      button.classList.toggle("active", selected);
      button.setAttribute("aria-selected", String(selected));
    });
    document.querySelectorAll("[data-panel]").forEach(panel => {
      panel.hidden = panel.dataset.panel !== activeTab;
    });
    status.textContent = "";
    status.classList.remove("error");
    results.replaceChildren();
  }));

  const rating = $("#target-rating");
  if (rating) rating.addEventListener("input", () => { $("#rating-value").textContent = Number(rating.value).toFixed(1); });
})();

(function () {
  if (!window.CTFd) return;

  const banner = document.createElement("div");
  banner.id = "rounds-banner";
  banner.style.cssText =
    "position:sticky;top:56px;z-index:1000;padding:10px 16px;text-align:center;font-weight:600;";
  const main = document.querySelector("main");
  if (main) main.prepend(banner);

  let remaining = null;
  let state = null;
  let name = "";

  function paint() {
    const clock =
      remaining == null
        ? ""
        : " · " +
          String(Math.floor(remaining / 60)).padStart(2, "0") +
          ":" +
          String(remaining % 60).padStart(2, "0");
    if (!name) {
      banner.textContent = "Waiting for the next round. Challenges open together.";
      banner.style.background = "#e9ecef";
      banner.style.color = "#212529";
      return;
    }
    if (state === "frozen") {
      banner.textContent = name + " is frozen. Submissions are paused." + clock;
      banner.style.background = "#ffc107";
      banner.style.color = "#212529";
      return;
    }
    banner.textContent = name + clock + " · early solves earn extra points";
    banner.style.background = "#0d6efd";
    banner.style.color = "#fff";
  }

  async function refresh() {
    try {
      const response = await CTFd.fetch("/api/v1/plugins/ctfd-rounds/status");
      const data = await response.json();
      if (!data.success || !data.round) {
        name = "";
        remaining = null;
        state = null;
      } else {
        name = data.round.name;
        state = data.round.state;
        remaining = data.round.remaining;
      }
      paint();
    } catch (err) {
      banner.textContent = "";
    }
  }

  setInterval(function () {
    if (state === "running" && remaining > 0) {
      remaining -= 1;
      paint();
    }
  }, 1000);
  refresh();
  setInterval(refresh, 15000);

  function challengeId() {
    const store = window.Alpine && Alpine.store && Alpine.store("challenge");
    return store && store.data && store.data.id;
  }

  async function launch(id, box) {
    const button = box.querySelector("button");
    button.disabled = true;
    button.textContent = "Building your instance...";
    try {
      const response = await CTFd.fetch(
        "/api/v1/plugins/ctfd-rounds/instance?challenge_id=" + id,
        { method: "POST" }
      );
      const data = await response.json();
      if (!data.success) {
        box.querySelector(".rounds-msg").textContent = data.message || "Could not launch.";
        button.disabled = false;
        button.textContent = "Launch instance";
        return;
      }
      box.querySelector(".rounds-msg").innerHTML =
        data.message +
        ' <a class="btn btn-sm btn-success ms-2" href="' +
        data.download +
        '">Download files</a>';
      button.textContent = "Instance ready";
    } catch (err) {
      box.querySelector(".rounds-msg").textContent = "Could not launch the instance.";
      button.disabled = false;
      button.textContent = "Launch instance";
    }
  }

  function inject() {
    const id = challengeId();
    const host = document.querySelector(".challenge-desc");
    if (!id || !host) return;
    if (host.querySelector("#rounds-instance[data-id='" + id + "']")) return;
    const old = document.getElementById("rounds-instance");
    if (old) old.remove();
    const box = document.createElement("div");
    box.id = "rounds-instance";
    box.dataset.id = String(id);
    box.className = "card mt-3";
    box.innerHTML =
      '<div class="card-body">' +
      "<h5>Your instance</h5>" +
      "<p class=\"mb-2\">Files and the flag are unique to your team. Create a team first, even if you are playing alone.</p>" +
      '<button type="button" class="btn btn-primary">Launch instance</button>' +
      '<div class="rounds-msg mt-2"></div></div>';
    box.querySelector("button").addEventListener("click", function () {
      launch(id, box);
    });
    host.appendChild(box);
  }

  setInterval(inject, 500);
})();

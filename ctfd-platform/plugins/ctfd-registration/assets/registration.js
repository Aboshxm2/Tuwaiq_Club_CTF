(function () {
  const path = window.location.pathname;
  if (path !== "/register" && path !== "/teams/new") return;

  const LEVELS = ["Beginner", "Intermediate", "Advanced"];

  function upgradeLevel() {
    const label = Array.from(document.querySelectorAll("label")).find(
      (el) => el.textContent.trim() === "Level"
    );
    if (!label) return;
    const input = document.getElementById(label.htmlFor);
    if (!input || input.tagName !== "INPUT") return;

    const select = document.createElement("select");
    select.id = input.id;
    select.name = input.name;
    select.required = true;
    select.className = "form-select";

    const placeholder = new Option("Choose your level", "");
    placeholder.disabled = true;
    select.add(placeholder);
    for (const level of LEVELS) select.add(new Option(level, level));
    select.value = LEVELS.includes(input.value) ? input.value : "";

    input.replaceWith(select);
  }

  // The server sets the team's bracket from its members' levels, so the
  // bracket picker CTFd adds to the new-team form is replaced with a note.
  function replaceBracketPicker() {
    const select = document.querySelector("select[name='bracket_id']");
    if (!select) return;
    // CTFd renders the label block, the select and its description as
    // loose siblings inside the form, so remove each one.
    const label = document.querySelector("label[for='bracket_id']");
    const labelBlock = label && label.closest("div");
    if (labelBlock && labelBlock.parentElement === select.parentElement) labelBlock.remove();
    const description = select.nextElementSibling;
    if (description && description.matches("small.form-text")) description.remove();
    const note = document.createElement("p");
    note.className = "form-text mb-3";
    note.textContent =
      "Your team's leaderboard (Beginner, Intermediate or Advanced) is the level " +
      "of its most experienced member. It updates when members join or leave.";
    select.replaceWith(note);
  }

  function run() {
    if (path === "/register") upgradeLevel();
    else replaceBracketPicker();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
})();

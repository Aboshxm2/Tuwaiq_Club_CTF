(function () {
  if (window.location.pathname !== "/register") return;

  const LEVELS = ["Beginner", "Intermediate", "Advanced"];

  function upgrade() {
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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", upgrade);
  } else {
    upgrade();
  }
})();

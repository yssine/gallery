const input = document.querySelector("#photos");
const dropzone = document.querySelector("#dropzone");
const fileList = document.querySelector("#file-list");
if (input && dropzone) {
  const showFiles = () => {
    const files = [...input.files];
    fileList.textContent = files.length ? `${files.length} frame${files.length === 1 ? "" : "s"} selected` : "";
    dropzone.classList.toggle("has-files", files.length > 0);
  };
  input.addEventListener("change", showFiles);
  ["dragenter", "dragover"].forEach(event => dropzone.addEventListener(event, e => { e.preventDefault(); dropzone.classList.add("dragging"); }));
  ["dragleave", "drop"].forEach(event => dropzone.addEventListener(event, e => { e.preventDefault(); dropzone.classList.remove("dragging"); }));
  dropzone.addEventListener("drop", e => { input.files = e.dataTransfer.files; showFiles(); });
}
document.querySelectorAll(".copy-link").forEach(button => button.addEventListener("click", async () => {
  await navigator.clipboard.writeText(button.dataset.link);
  const label = button.innerHTML; button.innerHTML = "Link copied <span>✓</span>";
  setTimeout(() => button.innerHTML = label, 2200);
}));

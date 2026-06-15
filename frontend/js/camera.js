export function initCamera(onCapture) {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = "image/*";
  input.capture = "environment";
  input.onchange = () => {
    const file = input.files?.[0];
    if (file) onCapture(file);
  };
  input.click();
}

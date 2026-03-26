function showMessage(id, message) {
    const messageElement = document.getElementById(id);
    messageElement.innerText = message;
    messageElement.style.display = "block";
}

function hideMessage(id) {
    const messageElement = document.getElementById(id);
    messageElement.innerText = "";
    messageElement.style.display = "none";
}
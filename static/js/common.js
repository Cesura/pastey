function copyToClipboard() {
    var copyText = document.getElementById("paste-url");
    copyText.select();
    copyText.setSelectionRange(0, 99999);
    document.execCommand("copy");
}

function setTheme(theme) {
    document.cookie = "pastey_theme=" + theme + "; Expires=Thu, 01 Jan 2100 00:00:01 GMT; path=/; SameSite=Lax;";
    location.reload();
}

function resetTheme() {
    document.cookie = "pastey_theme=; Expires=Thu, 01 Jan 1970 00:00:01 GMT; path=/; SameSite=Lax;";
    location.reload();
}

function copyToClipboard() {
    var copyText = document.getElementById("paste-url");
    copyText.select();
    copyText.setSelectionRange(0, 99999);
    document.execCommand("copy");
}
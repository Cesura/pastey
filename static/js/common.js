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

function decryptPaste() {
    var key = window.location.hash.substring(1);
    $("#paste-url").val($("#paste-url").val() + window.location.hash);

    try {
        var secret = new fernet.Secret(decodeURIComponent(key));

        // Decrypt title
        var title_token = new fernet.Token({
            secret: secret,
            token: $("#pastey-title").text(),
            ttl: 0
        });
        var title = title_token.decode();
        $("#pastey-title").text(title);
        document.title = title + ' | Pastey';

        // Decrypt content
        var content_token = new fernet.Token({
            secret: secret,
            token: $("#pastey-content").text(),
            ttl: 0
        });
        $("#pastey-content").text(content_token.decode());

        // Show success message
        $("#pastey-decrypt-success").css("display", "block");

    } catch(error) {

        // Show error message
        $("#pastey-decrypt-failed").css("display", "block");
    }
    
}
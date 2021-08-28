function refreshPage() {
    const longPollTimeout = 1000 * 60 * 10; // 10 minutes

    var xmlHttp = new XMLHttpRequest();
    xmlHttp.timeout = longPollTimeout;
    xmlHttp.onreadystatechange = () => { 
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
            console.log("Received refresh signal, refreshing page...");
            result = JSON.parse(xmlHttp.response);
            if (result["refresh"] == true) {
                fetch(window.location.href).then(response => {
                    response.text().then(html => {
                        document.open();
                        document.write(html);
                        document.close()
                    });
                });
            }
        }
    }

    xmlHttp.ontimeout = () => { refreshPage() };
    xmlHttp.onerror = () => { refreshPage() };
    xmlHttp.onabort = () => { refreshPage() };

    // Shouldn't be hardcoded
    xmlHttp.open("GET", "http://localhost:<port>/_refresh/long_poll", true);
    xmlHttp.send(null);
}

refreshPage();
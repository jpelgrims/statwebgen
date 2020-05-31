function refreshPage()
{
    const longPollTimeout = 1000 * 60 * 10; // 10 minutes

    var xmlHttp = new XMLHttpRequest();
    xmlHttp.timeout = longPollTimeout;
    xmlHttp.onreadystatechange = function() { 
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
            console.log("Received refresh signal, refreshing page...");
            result = JSON.parse(xmlHttp.response);
            if (result["refresh"] == true) {

                fetch(window.location.href)
                    .then(response => {
                        response.text().then(html => {
                            document.open();
                            document.write(html);
                            document.close()
                        });
                    });
                //window.location.reload(1);
            }
        }
        setTimeout(refreshPage, longPollTimeout);
    }
    xmlHttp.open("GET", "http://localhost:8001/_refresh", true);
    xmlHttp.send(null);
}

refreshPage();
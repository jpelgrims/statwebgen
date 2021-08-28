import http from 'http';
import url from 'url';
import { promises as fsPromises} from "fs";
import fs from "fs";
import path from 'path';
import FileProcessor from './file_processor.js';

const fileExtensionToContentType = {
    "pdf": "application/pdf",
    "css": "text/css",
    "js": "application/javascript",
    "html": "text/html",
    "txt": 'text/plain',
    "gif": "image/gif",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png"
}

const REFRESH_SCRIPT_PATH = path.resolve(path.dirname(url.fileURLToPath(import.meta.url)), 'live_refresh.js'); 

function urlToPath(requestUrl, baseDirectory) {
    let filePath;
    const decodedRequestUrl = decodeURI(requestUrl);

    if (decodedRequestUrl === '/') {
        filePath='/index.html'
    } else if (!decodedRequestUrl.split('/').pop().includes(".")) {
        filePath=decodedRequestUrl+'.html';
    } else {
        filePath = decodedRequestUrl;
    }

    // need to use path.normalize so people can't access directories underneath baseDirectory
    const fsPath = path.resolve(baseDirectory) + path.normalize(filePath);
    return fsPath;
}

const websiteRequestHandler = async (request, response, server) => {
    const fsPath = urlToPath(request.url, server.baseDirectory);
    
    // Load live refresh script
    let script = await fsPromises.readFile(REFRESH_SCRIPT_PATH, 'utf-8', (err, data) => {return data;});
    script = '<script>' + script.replace("<port>", server.port) + '</script>';

    let fileStream = fs.createReadStream(fsPath);

    fileStream.on('open', function () {
        const contentType = fileExtensionToContentType[fsPath.split(".").pop()] ?? "application/octet-stream";
        response.setHeader('Content-Type', contentType);

        if (server.liveRefresh && fsPath.endsWith(".html")) {
            // Insert the live-refresh script into every html page we serve
            const fileProcessorStream = new FileProcessor(script);
            server.currentUrl = request.url;
            fileStream.pipe(fileProcessorStream).pipe(response);
        } else {
            fileStream.pipe(response);
        }
    });

    fileStream.on('error',function(e) {
        console.log(e);
        response.setHeader('Content-Type', 'text/plain');
        response.writeHead(404); // Assume the file doesn't exist
        response.end();
    });
};

// Long polling
const liveRefreshHandler = async (request, response, server) => {
    if (request.url === "/_refresh/long_poll") {
        const filePath = urlToPath(server.currentUrl, server.baseDirectory);
        console.log(`[Internal]: Now watching ${server.currentUrl}, will refresh on changes`);

        // Remove the previous watcher, otherwise it will keep on running even though
        // we don't use it anymore 
        if (server.currentWatch) {
            fs.unwatchFile(server.currentWatch);
        }

        fs.watchFile(filePath, {persistent:false, interval: 100}, (event, trigger) => {
            console.log(`[Internal]: ${server.currentUrl} changed on disk, refreshing`);
            server.currentWatch = server.filePath;
            response.writeHead(200, {'Content-Type': 'application/json'});
            response.write(JSON.stringify({'refresh': true}));
            response.end();
        });
    }
};

function urlMatch(urlPattern, url) {
    const regex = urlPattern.replace(/\*/g, "[^ ]*");
    let regexp = new RegExp(regex);
    return regexp.test(url);
}

const requestListener = async function (request, response) {
    try {
        for (const [urlPattern, requestHandler] of Object.entries(this.requestHandlers)) {
            if (urlMatch(urlPattern, request.url)) {
                requestHandler(request, response, this);
                return;
            }
        }
        // Handle all requests that fell through
        this.defaultHandler(request, response, this);
        console.log(`[Request => 200]: ${request.url}`);
   } catch(e) {
        response.writeHead(500);
        response.end();     // end the response so browsers don't hang
        console.log(e.stack);
        console.log(`[Request => 500]: ${request.url}`);
   }
};

export default function createServer(folder) {
    let httpServer = http.createServer(requestListener);
    httpServer.port = 5000;
    httpServer.liveRefresh = false;
    httpServer.baseDirectory = folder;
    httpServer.lastChanges = 0;
    httpServer.currentUrl = "/";
    httpServer.currentWatch;
    httpServer.requestHandlers = {
        "/_refresh/*": liveRefreshHandler
    };
    httpServer.defaultHandler = websiteRequestHandler;
    httpServer.enableAutoRefresh = () => { httpServer.liveRefresh = true };
    httpServer.run = (port) => { 
        httpServer.port = port;
        httpServer.listen(port); };
    return httpServer;
};


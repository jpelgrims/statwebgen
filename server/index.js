import yargs from 'yargs';
import createServer from './server.js';

yargs
.command('serve [port]', 'Run a development server', (yargs) => {
    yargs.positional('port', {describe: 'port to bind on', default: 5000})}, (argv) => {
        if (argv.verbose) {console.info(`start server on :${argv.port}`)};

        const directory = argv.path ? argv.path : process.cwd();

        const server = createServer(directory);
        if (argv.autorefresh) {
            server.enableAutoRefresh();
        }

        server.listen(argv.port);
})
.option('path', {
    alias: 'p',
    type: 'string',
    description: "path to a directory to serve"
})
.option('autorefresh', {
    alias: 'r',
    type: 'boolean',
    description: 'Automatically reload current page on changes'
})
.option('verbose', {
    alias: 'v',
    type: 'boolean',
    description: 'Run with verbose logging'
})
.argv
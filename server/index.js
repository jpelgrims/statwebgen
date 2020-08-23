import yargs from 'yargs';
import createServer from './server.js';

yargs
.command('serve [port]', 'Run a development server', (yargs) => {
    yargs.positional('port', {describe: 'port to bind on', default: 5000})}, (argv) => {

        const directory = argv.path ? argv.path : process.cwd();

        const server = createServer(directory);
        if (argv.autorefresh) {
            server.enableAutoRefresh();
        }

        console.info(`Dev-server running on port ${argv.port}, serving from from ${directory}`)

        server.run(argv.port);
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
.argv
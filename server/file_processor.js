import { Transform } from 'stream';

export default class FileProcessor extends Transform {
    script;

    constructor(script) {
        // This setting allow to pass of js Objects, in addition to e.g string and Buffer
        super({ writableObjectMode: true });
        this.script = script;
    }

    transformLine

    async _transform(chunk, _encoding, callback) {
        try {
            let data = chunk.toString();
            let transformedData = data;

            let insertPosition = data.search("</head>");
            if (insertPosition) {
                transformedData = data.slice(0, insertPosition) + this.script + data.slice(insertPosition);
            }

            callback(undefined, transformedData);
        } catch (e) {
            callback(e);
        }
    }
}
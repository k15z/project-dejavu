var fs = require('fs');
var crypto = require('crypto')
var rimraf = require('rimraf');
var multer = require('multer');
var express = require('express');
var bodyParser = require('body-parser');
var exec = require('child_process').exec;
var mongo = require('mongodb').MongoClient;

var app = express();
app.listen(8080);

app.use(bodyParser.urlencoded({ extended: false }))
app.use(bodyParser.json())
app.use('/', express.static(__dirname + '/public'));
app.use('/uploads', express.static(__dirname + '/uploads'));

app.get('/', function (req, res) {
    res.sendFile(__dirname + '/public/index.html');
});
app.get('/app', function (req, res) {
    res.sendFile(__dirname + '/public/capture.html');
});
app.get('/upload', function (req, res) {
    res.sendFile(__dirname + '/public/upload.html');
});

mongo.connect('mongodb://localhost:27017/dejavu', function(err, db) {
    if (err)
        throw 'Database connection failed.'

    app.get('/api/reset', function (req, res) {
        rimraf(__dirname + "/uploads/*", function () {});
        db.collection('content').remove({}, function (err) {
            res.send("done.")
        });
    });

    app.get('/api/content', function (req, res) {
        db.collection('content').find().toArray(function (err, content) {
            res.send(content);
        });
    });

    var storage = multer.diskStorage({
        destination: function (req, file, cb) {
            cb(null, 'uploads/')
        },
        filename: function (req, file, cb) {
            crypto.pseudoRandomBytes(16, function (err, raw) {
                cb(null, raw.toString('hex') + Date.now() + '.mp4');
            });
        }
    });
    app.post('/api/upload', multer({'storage': storage}).single('video'), function (req, res) {
        if (!req.body.label || req.body.lable.length == 0)
            req.body.label = req.file.originalname
        var content = {
            'label': req.body.label,
            'video': req.file.path,
            'image': req.file.path + '.jpg',
            'djv': req.file.path + '.djv'
        }
        exec('python dejavu.py vectorize ' + content.video + ' ' + content.djv);
        exec('ffmpeg -i ' + content.video + ' -ss 00:00:20 -vframes 1 ' + content.image);
        db.collection('content').insert(content, function (err, content) {
            res.send(content);
        });
    });

    var capture = {};
    app.all('/api/capture', function (req, res) {
        var cid = Math.random().toString(36).substring(2, 10);
        capture[cid] = [];
        res.send({
            'cid': cid,
            'capture': capture[cid]
        })
    });
    app.post('/api/capture/:cid', function (req, res) {
        var cid = req.params.cid;
        var file = cid + "." + capture[cid].length + ".png";
        capture[cid].push(file);
        fs.writeFile(
            __dirname + "/uploads/" + file, 
            req.body.image.replace(/^data:image\/png;base64,/, ""), 
            'base64',
            function (err) {
                res.send({
                    'cid': cid,
                    'capture': capture[cid]
                })
            }
        );
    });
    app.all('/api/capture/:cid/compute', function (req, res) {
        var cid = req.params.cid;
        var glob = "uploads/" + cid;
        exec('python dejavu.py recognize ' + glob + ' uploads', function(error, stdout, stderr) {
            db.collection('content').find().toArray(function (err, content) {
                lookup = {};
                for (var i = 0; i < content.length; i++)
                    lookup[content[i].djv] = content[i]
                var result = JSON.parse(stdout)
                for (var i = 0; i < result.length; i++)
                    result[i] = {
                        label: lookup[result[i][0]].label,
                        raw_json: result[i]
                    };
                res.send(result);
            });
        });
    });
});
rimraf(__dirname + "/uploads/*.png", function () {})

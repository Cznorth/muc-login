#!/usr/bin/env node
// Browser SM2 encryptor using original ca.muc.edu.cn sm2.min.js
global.window = global;
global.navigator = { userAgent: 'Node.js' };
global.btoa = s => Buffer.from(s, 'binary').toString('base64');
global.atob = s => Buffer.from(s, 'base64').toString('binary');
const fs = require('fs');
const code = fs.readFileSync('C:\\Users\\cznorth\\sm2.min.js', 'utf8');
eval(code);

const pubkey = "BMgXvoCLbC9cF8JAS/bv6Gd82+K+fFC2nRi7QJO3GvDkx0iLBmqDMpQUBxjC3yTfXN83cPVZRplPDsvr92K4omA=";
const pwd = process.argv[2];
if (!pwd) { console.error('Usage: node sm2-enc.js <password>'); process.exit(1); }
console.log(sm2.encrypt(pwd, pubkey));

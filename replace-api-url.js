const fs = require('fs');
const path = require('path');

const filesToUpdate = [
  path.join(__dirname, 'frontend', 'script.js'),
  path.join(__dirname, 'frontend', 'admin.html')
];

const productionUrl = 'https://draw-master.nelke.vip';

filesToUpdate.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  content = content.replace(/http:\/\/localhost:5050/g, productionUrl);
  fs.writeFileSync(file, content, 'utf8');
  console.log(`Updated API URL in ${file}`);
});
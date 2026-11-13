const https = require('https');
const fs = require('fs');
const path = require('path');

const outputDir = 'd:\\hipercool-refactor\\client\\public\\audio\\ambient';

const queries = {
  'office': 'office ambiance',
  'call_center': 'call center noise',
  'street': 'street traffic noise',
  'coffee_shop': 'coffee shop ambiance',
  'lofi_static': 'vinyl static noise'
};

async function download(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, (response) => {
      if (response.statusCode === 301 || response.statusCode === 302) {
        return download(response.headers.location, dest).then(resolve).catch(reject);
      }
      if (response.statusCode !== 200) {
        return reject(new Error(`Failed to get '${url}' (${response.statusCode})`));
      }
      response.pipe(file);
      file.on('finish', () => {
        file.close(resolve);
      });
    }).on('error', (err) => {
      fs.unlink(dest, () => reject(err));
    });
  });
}

async function searchArchive(query) {
  const url = `https://archive.org/advancedsearch.php?q=(${encodeURIComponent(query)})+AND+mediatype:audio&fl[]=identifier&sort[]=downloads+desc&rows=3&output=json`;
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch(e) {
          reject(e);
        }
      });
    }).on('error', reject);
  });
}

async function getMp3File(identifier) {
  const url = `https://archive.org/metadata/${identifier}`;
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          const files = json.files || [];
          const mp3 = files.find(f => f.name.endsWith('.mp3'));
          if (mp3) {
            resolve(`https://archive.org/download/${identifier}/${mp3.name}`);
          } else {
            resolve(null);
          }
        } catch(e) {
          resolve(null);
        }
      });
    }).on('error', reject);
  });
}

async function main() {
  for (const [key, query] of Object.entries(queries)) {
    console.log(`Searching for ${key} (${query})...`);
    try {
      const results = await searchArchive(query);
      const docs = results.response.docs;
      
      let downloaded = false;
      for (const doc of docs) {
        const mp3Url = await getMp3File(doc.identifier);
        if (mp3Url) {
          console.log(`Found MP3 for ${key}: ${mp3Url}`);
          const dest = path.join(outputDir, `${key}.mp3`);
          await download(mp3Url, dest);
          console.log(`Saved to ${dest}`);
          downloaded = true;
          break;
        }
      }
      
      if (!downloaded) {
        console.log(`No valid MP3 found for ${key}.`);
      }
    } catch(err) {
      console.error(`Error processing ${key}:`, err.message);
    }
  }
}

main();

const https = require('https');
const fs = require('fs');
const path = require('path');

const outputDir = 'd:\\hipercool-refactor\\client\\public\\audio\\ambient';

if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

const files = {
  'office.mp3': 'https://cdn.freesound.org/previews/339/339324_5121236-lq.mp3',
  'street.mp3': 'https://cdn.freesound.org/previews/173/173932_3110291-lq.mp3',
  'call_center.mp3': 'https://cdn.freesound.org/previews/347/347625_5121236-lq.mp3',
  'coffee_shop.mp3': 'https://cdn.freesound.org/previews/234/234733_4019029-lq.mp3',
  'lofi_static.mp3': 'https://cdn.freesound.org/previews/154/154133_2738739-lq.mp3',
};

function download(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    
    const options = {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Connection': 'keep-alive'
      }
    };

    https.get(url, options, (response) => {
      if (response.statusCode === 301 || response.statusCode === 302) {
        return download(response.headers.location, dest).then(resolve).catch(reject);
      }
      if (response.statusCode !== 200) {
        return reject(new Error(`Failed to get '${url}' (Status: ${response.statusCode})`));
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

async function main() {
  for (const [filename, url] of Object.entries(files)) {
    console.log(`Downloading ${filename}...`);
    try {
      await download(url, path.join(outputDir, filename));
      console.log(`Success: ${filename}`);
    } catch(err) {
      console.error(`Error downloading ${filename}:`, err.message);
    }
  }
}

main();

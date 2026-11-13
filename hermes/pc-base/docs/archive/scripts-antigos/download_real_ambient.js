const https = require('https');
const fs = require('fs');
const path = require('path');

const outputDir = 'd:\\hipercool-refactor\\client\\public\\audio\\ambient\\reais';

if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

// Hardcoded direct URLs to some known public domain / creative commons ambient noises on Archive.org or Wikimedia
const files = {
  'office.mp3': 'https://archive.org/download/aporee_11843_13337/11843_13337.mp3', // office / room ambience
  'call_center.mp3': 'https://archive.org/download/aporee_36224_42636/36224_42636.mp3', // talking / busy room
  'street.mp3': 'https://archive.org/download/aporee_34360_40114/34360_40114.mp3', // traffic / street
  'coffee_shop.mp3': 'https://archive.org/download/aporee_29054_33503/29054_33503.mp3', // cafe / people talking
};

function download(url, dest) {
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

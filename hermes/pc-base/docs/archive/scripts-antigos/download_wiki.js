const https = require('https');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const outputDir = 'd:\\hipercool-refactor\\client\\public\\audio\\ambient';

const files = {
  'office': 'https://upload.wikimedia.org/wikipedia/commons/4/4e/Office_ambience_with_keyboards_and_mouse.ogg',
  'street': 'https://upload.wikimedia.org/wikipedia/commons/e/ea/Traffic_noise_in_Tokyo.ogg',
  'coffee_shop': 'https://upload.wikimedia.org/wikipedia/commons/3/30/Restaurant_ambience.ogg',
  'call_center': 'https://upload.wikimedia.org/wikipedia/commons/6/69/Telephone_ringing.ogg',
  'lofi_static': 'https://upload.wikimedia.org/wikipedia/commons/9/9f/TV_static.ogg',
};

function download(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    const options = {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
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
  for (const [key, url] of Object.entries(files)) {
    console.log(`Downloading ${key}.ogg...`);
    const oggPath = path.join(outputDir, `${key}.ogg`);
    const mp3Path = path.join(outputDir, `${key}.mp3`);
    try {
      await download(url, oggPath);
      console.log(`Converting ${key}.ogg to ${key}.mp3...`);
      execSync(`ffmpeg -i "${oggPath}" -c:a libmp3lame -y "${mp3Path}"`);
      fs.unlinkSync(oggPath); // Clean up the OGG
      console.log(`Success: ${key}.mp3`);
    } catch(err) {
      console.error(`Error processing ${key}:`, err.message);
    }
  }
}

main();

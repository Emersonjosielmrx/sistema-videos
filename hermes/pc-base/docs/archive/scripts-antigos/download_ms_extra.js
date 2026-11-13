const https = require('https');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const outputDir = 'd:\\hipercool-refactor\\client\\public\\audio\\ambient';

const files = {
  'car': 'https://raw.githubusercontent.com/microsoft/MS-SNSD/master/noise_train/Car_1.wav',
  'restaurant': 'https://raw.githubusercontent.com/microsoft/MS-SNSD/master/noise_train/Restaurant_1.wav',
  'park': 'https://raw.githubusercontent.com/microsoft/MS-SNSD/master/noise_train/Park_1.wav',
  'airport': 'https://raw.githubusercontent.com/microsoft/MS-SNSD/master/noise_train/Airport_1.wav',
  'bus': 'https://raw.githubusercontent.com/microsoft/MS-SNSD/master/noise_train/Bus_1.wav'
};

function download(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, (response) => {
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
    console.log(`Downloading ${key}...`);
    const wavPath = path.join(outputDir, `${key}.wav`);
    const mp3Path = path.join(outputDir, `${key}.mp3`);
    try {
      await download(url, wavPath);
      console.log(`Converting to mp3...`);
      execSync(`ffmpeg -i "${wavPath}" -c:a libmp3lame -q:a 2 -y "${mp3Path}"`);
      fs.unlinkSync(wavPath);
      console.log(`Success: ${key}.mp3`);
    } catch(err) {
      console.error(`Error processing ${key}:`, err.message);
    }
  }
}

main();

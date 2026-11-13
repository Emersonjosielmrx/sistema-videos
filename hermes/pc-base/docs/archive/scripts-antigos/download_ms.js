const https = require('https');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const outputDir = 'd:\\hipercool-refactor\\client\\public\\audio\\ambient';

const files = {
  'coffee_shop': 'https://raw.githubusercontent.com/microsoft/MS-SNSD/master/noise_train/Cafe_1.wav',
  'street': 'https://raw.githubusercontent.com/microsoft/MS-SNSD/master/noise_train/Traffic_1.wav',
  'call_center': 'https://raw.githubusercontent.com/microsoft/MS-SNSD/master/noise_train/Babble_1.wav',
  'office': 'https://raw.githubusercontent.com/microsoft/MS-SNSD/master/noise_train/Typing_1.wav',
  'lofi_static': 'https://raw.githubusercontent.com/microsoft/MS-SNSD/master/noise_train/AirConditioner_1.wav'
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

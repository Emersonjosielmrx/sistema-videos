// SEED das chaves ElevenLabs no cofre (uso pessoal da dona). Arquivo git-ignored (deploy/).
// Insere cada chave como credential provider=elevenlabs, type=tts, com o nome dado.
// Idempotente: usa o Upsert por (user_id, name, type) do backend via API.
const crypto = require('crypto');
const BASE = 'https://hermescall.opus-sem-limites.com.br';
const SECRET = '<SEGREDO_REMOVIDO>';
const USER = '4e8adf4a-6530-47e2-af4c-1c268e6e68d7';

const KEYS = [
  ['emerosnmrx', 'sk_7e3e68e3ae859fc46abb0bbf9b72972998677a8423e69786'],
  ['volupe', 'sk_4928510d7a8ca8d0b2c033b9af1eb7b74cda28e9aa49a569'],
  ['haylla', 'sk_b4473ec0c94d6cce9be332f302f7f40f811d3a3a0011a899'],
  ['fabrica 0', 'sk_e58f8818c607e9836d79b393211f854f1538f8aa09ff3537'],
  ['fabrica', 'sk_31893d65a94183bb2a13418a2c6652a4337932ab3ac2da51'],
  ['fabio', 'sk_d02e0a60b343f5a4d98f3cccacff886af87224164deacee6'],
  ['ing', 'sk_df85144f0acc59dd1d6da957458d510dda408c4637812854'],
  ['jogos com ia', 'sk_08226ca1ebb56d2df695eee869be92c11fc32a54e81c4708'],
  ['emersongenshin', 'sk_e96cf058d7ca1cddd196c91a706b488353950de1658ee725'],
  ['manga verse', 'sk_d7955c520c6fbdabb200fd495c0e4eb07e16a4222cddcaac'],
  ['manga br', 'sk_f2e747c084200fe417cc1476af95ccebbbcf0f69afff9b07'],
  ['manga russian', 'sk_83cda767512ebb79efd132515003bdb16c4db74924335ac2'],
  ['manga seita', 'sk_4b53ef08feaca6655ffa603c837c678408c270b3fef4fff2'],
  ['manga fench', 'sk_a9950108507b814028ce61543e28466bd6d6816b970f29a8'],
  ['manga ind', 'sk_bc12f4a9e28b82d6e80aac5dc1b24358b134dfba76b08bd7'],
  ['manga hind', 'sk_f882cf81784a293b0737484e8a1d8f47b5042445964ed03e'],
  ['manga viet', 'sk_3eaf31f23ca1218775c333a2e0ef10897ee19f54a0de53a0'],
  ['manga tahi', 'sk_5ecbba34f8f4ed04b1690eb462353d29a6e571ae9a60b61f'],
  ['manga esp', 'sk_509aebd1129a8a273649872c1c195e82492876a8c34f9257'],
  ['emerson649', 'sk_e258e156937f555dcd4e3600ef82412b753c75b534017d1f'],
  ['canal alucina ai', 'sk_989c5e64c5fed6c2f70f5c9bd11ce78047c3eff93a99477d'],
  ['mundosolar1995', 'sk_88559780abf3e18bf67767d0756e0dfbb05e68f09f74aa99'],
  ['andre', 'sk_929ac1bf0d3d2914d981faaebb4556c5239142db10d11265'],
];

const b = s => Buffer.from(s).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
function jwt() {
  const n = Math.floor(Date.now() / 1e3);
  const h = b(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const p = b(JSON.stringify({ sub: USER, iat: n, exp: n + 3600 }));
  const s = b(crypto.createHmac('sha256', SECRET).update(h + '.' + p).digest());
  return `${h}.${p}.${s}`;
}

(async () => {
  let ok = 0, fail = 0;
  for (const [name, key] of KEYS) {
    try {
      const r = await fetch(BASE + '/api/credentials', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + jwt(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'eleven ' + name, type: 'tts', provider: 'elevenlabs', api_key: key }),
      });
      if (r.ok) { ok++; console.log(`OK   ${name}`); }
      else { fail++; console.log(`FAIL ${name} -> ${r.status} ${(await r.text()).slice(0, 80)}`); }
    } catch (e) { fail++; console.log(`ERR  ${name} -> ${e.message}`); }
  }
  console.log(`\nTotal: ${ok} inseridas, ${fail} falhas.`);
})();

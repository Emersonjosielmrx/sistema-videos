#!/usr/bin/env node
/**
 * RELEASE — versionamento GitHub + Docker Hub (Hermes Call)
 * ==========================================================
 * Um comando pra cortar uma release versionada, com canais e stack de tags.
 *   1. Lê a versão do arquivo VERSION (raiz), ex.: 0.2.0 ou 0.2.0-beta.1.
 *   2. Cria a tag Git `vX.Y.Z[-beta.N]` e faz push pro GitHub.
 *   3. Builda a imagem Docker e faz push pro Docker Hub com a STACK DE TAGS do canal:
 *
 *        Canal stable (produção):
 *          DOCKERHUB_REPO:vX.Y.Z    (fixa, imutável — pin/rollback determinístico)
 *          DOCKERHUB_REPO:stable    (móvel — última estável)
 *          DOCKERHUB_REPO:latest    (móvel — convenção: latest == estável)
 *
 *        Canal beta (validação / pré-lançamento):
 *          DOCKERHUB_REPO:vX.Y.Z-beta.N  (fixa, imutável)
 *          DOCKERHUB_REPO:next            (móvel — próxima a validar)
 *          DOCKERHUB_REPO:beta            (móvel — alias de next)
 *          → NÃO toca em :latest (produção fica intocada).
 *
 * Qual tag puxar:
 *   - Produção estável:            docker pull DOCKERHUB_REPO:latest  (ou :stable)
 *   - Testar a próxima (beta):     docker pull DOCKERHUB_REPO:next    (ou :beta)
 *   - Fixar uma versão exata:      docker pull DOCKERHUB_REPO:v0.2.0
 *
 * Credenciais e config vêm de deploy/.env.deploy (NUNCA versionado).
 * O build da imagem roda no ambiente onde você chamar isto (precisa de Docker).
 * Se o seu PC não tem Docker, rode este script NA VPS (que tem Docker).
 *
 * Uso:
 *   node deploy/release.js                          # versão do VERSION; canal inferido
 *   node deploy/release.js --version 0.2.0          # release estável 0.2.0
 *   node deploy/release.js --version 0.2.0-beta.1   # pré-lançamento (canal beta auto)
 *   node deploy/release.js --version 0.2.0 --channel beta  # força canal
 *   node deploy/release.js --no-git                 # só builda/push Docker
 *   node deploy/release.js --no-docker              # só cria/push a tag Git
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

// ---- Carrega .env.deploy (KEY=VALUE por linha) ----
function loadEnv() {
  const p = path.join(__dirname, '.env.deploy');
  if (!fs.existsSync(p)) {
    console.error('FALTA deploy/.env.deploy — copie de deploy/.env.deploy.example e preencha.');
    process.exit(1);
  }
  const env = {};
  for (const line of fs.readFileSync(p, 'utf8').split('\n')) {
    const s = line.trim();
    if (!s || s.startsWith('#')) continue;
    const i = s.indexOf('=');
    if (i === -1) continue;
    env[s.slice(0, i).trim()] = s.slice(i + 1).trim();
  }
  return env;
}

function sh(cmd, opts = {}) {
  console.log('  $ ' + cmd.replace(/(-p|--password[= ])\S+/g, '$1***'));
  return execSync(cmd, { stdio: 'inherit', cwd: ROOT, ...opts });
}
function shOut(cmd) {
  return execSync(cmd, { cwd: ROOT }).toString().trim();
}

function arg(name) {
  const i = process.argv.indexOf(name);
  return i !== -1 ? process.argv[i + 1] : null;
}
const NO_GIT = process.argv.includes('--no-git');
const NO_DOCKER = process.argv.includes('--no-docker');

// Canal da release. Determina a STACK DE TAGS movíveis no Docker Hub:
//   stable → :vX.Y.Z (fixa/imutável) + :stable + :latest   (produção; latest = estável)
//   beta   → :vX.Y.Z-beta.N (fixa)   + :next + :beta        (validação; NÃO mexe em :latest)
// Regra: `:latest` só aponta pra ESTÁVEL. Quem quer testar puxa `:next` (ou `:beta`).
// A versão exata (:vX.Y.Z[-beta.N]) é sempre imutável, pra pin/rollback determinístico.
function resolveChannel() {
  const c = (arg('--channel') || '').toLowerCase();
  if (c === 'stable' || c === 'beta') return c;
  return null; // será inferido pelo sufixo de pré-lançamento
}

function main() {
  const env = loadEnv();

  // ---- Versão ----
  let version = arg('--version');
  const versionFile = path.join(ROOT, 'VERSION');
  if (version) {
    fs.writeFileSync(versionFile, version + '\n');
    console.log('[version] VERSION atualizado para ' + version);
  } else {
    version = fs.readFileSync(versionFile, 'utf8').trim();
  }
  // Aceita X.Y.Z e pré-lançamentos X.Y.Z-beta.N / -rc.N / -alpha.N (SemVer pre-release).
  if (!/^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$/.test(version)) {
    console.error('Versão inválida: "' + version + '" (esperado X.Y.Z ou X.Y.Z-beta.N).');
    process.exit(1);
  }
  const tag = 'v' + version;

  // Canal: --channel vence; senão infere do sufixo (-beta/-rc/-alpha => beta); senão stable.
  const isPre = /-/.test(version);
  const channel = resolveChannel() || (isPre ? 'beta' : 'stable');
  console.log('=== RELEASE ' + tag + ' (canal: ' + channel + ') ===\n');

  // ---- 1. Git tag + push ----
  if (!NO_GIT) {
    console.log('[git] criando tag ' + tag + ' e enviando pro GitHub...');
    const existing = shOut('git tag --list ' + tag);
    if (existing) {
      console.log('  tag ' + tag + ' já existe localmente — pulando criação.');
    } else {
      sh('git tag -a ' + tag + ' -m "release ' + tag + ' (' + channel + ')"');
    }
    sh('git push origin ' + tag);
  }

  // ---- 2. Docker build + push ----
  if (!NO_DOCKER) {
    const repo = env.DOCKERHUB_REPO;
    const user = env.DOCKERHUB_USER;
    const token = env.DOCKERHUB_TOKEN;
    if (!repo || !user || !token) {
      console.error('Faltam DOCKERHUB_REPO/USER/TOKEN em deploy/.env.deploy');
      process.exit(1);
    }

    // Stack de tags conforme o canal.
    const imgVer = repo + ':' + tag; // sempre: versão exata, imutável
    const movable = channel === 'stable'
      ? [repo + ':stable', repo + ':latest'] // estável move :stable e :latest
      : [repo + ':next', repo + ':beta'];    // beta move :next e :beta (NUNCA :latest)
    const allTags = [imgVer, ...movable];

    console.log('\n[docker] login no Docker Hub como ' + user + '...');
    // login via stdin pra não deixar o token no histórico de processos.
    execSync('docker login -u ' + user + ' --password-stdin', { cwd: ROOT, input: token, stdio: ['pipe', 'inherit', 'inherit'] });

    const tagFlags = allTags.map(t => '-t ' + t).join(' ');
    console.log('[docker] build ' + allTags.join(', ') + ' (compila MLow + client + Go)...');
    sh('docker build ' + tagFlags + ' .');

    console.log('[docker] push das tags...');
    for (const t of allTags) sh('docker push ' + t);
  }

  console.log('\n=== RELEASE ' + tag + ' OK (' + channel + ') ===');
  if (!NO_GIT) console.log('  GitHub: tag ' + tag + ' publicada.');
  if (!NO_DOCKER) {
    const movable = channel === 'stable' ? ':stable + :latest' : ':next + :beta (latest intacto)';
    console.log('  Docker Hub: ' + env.DOCKERHUB_REPO + ':' + tag + ' + ' + movable + '.');
  }
}

main();

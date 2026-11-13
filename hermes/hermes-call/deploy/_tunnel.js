const {Client}=require('ssh2');const net=require('net');const fs=require('fs');
const env=fs.readFileSync('.env.deploy','utf8');
const host=(env.match(/HERMES_VPS_HOST=(.+)/)||[])[1].trim();
const pass=(env.match(/HERMES_VPS_PASS=(.+)/)||[])[1].trim();
const c=new Client();
c.on('ready',()=>{
  const srv=net.createServer(sock=>{c.forwardOut('127.0.0.1',0,'127.0.0.1',8092,(err,stream)=>{if(err){sock.end();return;}sock.pipe(stream).pipe(sock);});});
  srv.listen(8092,'127.0.0.1',()=>console.log('TUNNEL_READY'));
});
c.on('error',e=>console.error('SSH ERR',e.message));
c.connect({host,port:22,username:'root',password:pass,readyTimeout:30000,keepaliveInterval:15000});

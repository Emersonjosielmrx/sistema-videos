# uso: bash aplica_sql.sh arquivo.sql  (roda no banco apps_aulas como o usuário aulas)
set -e
scp -q "$1" hermes-bloqueio:/tmp/_aplica.sql
ssh hermes-bloqueio 'C=$(docker ps -q -f name=postgres2_postgres2); docker cp /tmp/_aplica.sql $C:/tmp/_aplica.sql; docker exec $C psql -q -U aulas -d apps_aulas -v ON_ERROR_STOP=1 -f /tmp/_aplica.sql; R=$?; docker exec $C rm -f /tmp/_aplica.sql; rm -f /tmp/_aplica.sql; exit $R'

#!/usr/bin/env bash
# Uso: bash send_oo.sh ETAPA ESTADO ARCHIVO_LOG
STAGE="$1"; STATUS="$2"; FILE="$3"
[ -f "$FILE" ] || echo "(sin salida registrada)" > "$FILE"

sed 's/\x1b\[[0-9;]*m//g'DAM "$FILE" | tail -n 150 | jq -R -s -c \
  --arg stage "$STAGE" --arg status "$STATUS" \
  --arg commit "$GITHUB_SHA" --arg branch "$GITHUB_REF_NAME" \
  --arg user "$GITHUB_ACTOR" --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg run "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID" \
  'split("\n") | map(select(length>0)) | to_entries | map({
     timestamp:$ts, event:"PIPELINE_LOG", stage:$stage, status:$status,
     line:(.key+1), message:.value, commit:$commit, branch:$branch,
     user:$user, run_url:$run })' \
| curl -s --max-time 20 -X POST "$OPENOBSERVE_URL/api/default/cicd_pipeline/_json" \
    -H "Content-Type: application/json" \
    -H "Authorization: $OPENOBSERVE_AUTH" -d @- \
|| echo "No se pudo enviar a OpenObserve"
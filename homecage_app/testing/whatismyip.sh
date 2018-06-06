myIP=$(hostname -I) || true
if [ "$myIP" ]; then
  echo "$myIP"
fi

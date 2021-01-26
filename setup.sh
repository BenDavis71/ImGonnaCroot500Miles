mkdir -p ~/.streamlit/
echo "[general]
email = \"bendavis71@Knights.ucf.edu\"
" > ~/.streamlit/credentials.toml
echo "[server]
headless = true
port = $PORT
enableCORS = false
" > ~/.streamlit/config.toml

### Instructions

- build from project root: `docker build -t tova .`
- run: `docker run -d --rm -p 80:80 -p 443:443 --name tova tova`
- request: `curl -k https://localhost/http/example.com/challenge`

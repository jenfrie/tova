#base
FROM nginx:latest
RUN apt update && apt upgrade -y && apt autoremove -y

#python
RUN apt install python3 python3-pip -y
RUN apt install procps -y

#nginx
COPY config/nginx.conf /etc/nginx/conf.d/server.conf
COPY config/server.crt /etc/nginx/certs/server.crt
COPY config/server.key /etc/nginx/certs/server.key

#tor
RUN apt install tor -y
COPY config/torrc /etc/tor/torrc

#app
RUN pip install stem requests[socks] flask gunicorn UltraDict --break-system-packages --no-cache-dir
COPY src/ /app/
RUN mkdir -p /app/logs/

#env
ENV CIRCUIT_TTL=180
ENV REQUEST_TIMEOUT=30
ENV WORKER_TIMEOUT=60
ENV VAL_K=5
ENV VAL_N=7
ENV N_CIRCUITS=50
ENV PREFIX_LEN=9
ENV BUILD_TIMEOUT=15

CMD export CORES=$(if egrep -q '^max' /sys/fs/cgroup/cpu.max; then nproc; else egrep -o '^[0-9]*' /sys/fs/cgroup/cpu.max | sed 's/00000//'; fi) && sed -i "s/worker_processes.*;/worker_processes $CORES;/" /etc/nginx/nginx.conf && nginx -t && service nginx start && (tor -f /etc/tor/torrc &) && sleep 20s && cd /app/ && (python3 circus.py  &) && gunicorn --bind unix:/tmp/gunicorn.sock --workers $CORES --timeout $WORKER_TIMEOUT tova:app

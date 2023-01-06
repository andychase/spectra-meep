docker build -t sm -f app_Dockerfile .
SM_TAG=$(docker run -d sm)
sleep 20
docker checkpoint create --checkpoint-dir=/snaps $SM_TAG my_checkpoint
docker cp $SM_TAG:/tmp/. /snaps/tmp/

SM_TAG=$(docker run -d sm)
sleep 5
docker stop $SM_TAG
docker cp /snaps/tmp/. $SM_TAG:/tmp/

cp -r /snaps/my_checkpoint /var/lib/docker/containers/$SM_TAG/checkpoints/
docker start --checkpoint=my_checkpoint $SM_TAG

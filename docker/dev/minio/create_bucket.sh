until /usr/bin/mc alias set dockerminio http://minio-s3:9000 "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"; do
    echo "Minio not ready, start again in 2seconds. ${MINIO_ROOT_USER}"
    sleep 2
done

/usr/bin/mc mb dockerminio/${MINIO_BUCKET_NAME} --ignore-existing;
exit 0;

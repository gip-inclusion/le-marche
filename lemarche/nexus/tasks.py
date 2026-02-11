from huey.contrib.djhuey import task

from lemarche.nexus import sync


@task()
def async_sync_users(users):
    sync.sync_users(users)


@task()
def async_delete_users(user_pks):
    sync.delete_users(user_pks)


@task()
def async_sync_siaes(siaes):
    sync.sync_siaes(siaes)


@task()
def async_delete_siaes(siae_pks):
    sync.delete_siaes(siae_pks)


@task()
def async_sync_siaeusers(siaeusers):
    sync.sync_siaeusers(siaeusers)


@task()
def async_delete_siaeusers(siaeuser_pks):
    sync.delete_siaeusers(siaeuser_pks)

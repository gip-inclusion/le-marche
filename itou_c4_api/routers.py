# Info : https://www.protechtraining.com/blog/post/tutorial-using-djangos-multiple-database-support-477 
class CocoRouter(object):
    def db_for_read(self, model, **hints):
        "Point all operations on cocorico models to 'structures'"
        # For those in a more audacious mood
        # return random.choice(['structures', 'default'])
        if model._meta.app_label == 'cocorico':
            return 'structures'
        return 'default'

    def db_for_write(self, model, **hints):
        "Point all operations on cocorico models to 'structures'"
        if model._meta.app_label == 'cocorico':
            return 'structures'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow if same DB
        if obj1._state.db == obj2._state.db:
            return True
        return False

    def allow_syncdb(self, db, model):
        # Disallow sync on cocorico database
        no_sync_dbs = ['structures']
        no_sync_apps = ['cocorico']

        if db in no_sync_dbs:
            return False

        if model._meta.app_label in no_sync_apps:
            return False

        return True

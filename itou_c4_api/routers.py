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
        # Don't allow, ever
        return False

    def allow_syncdb(self, db, model):
        # Don't allow, ever
        return False
